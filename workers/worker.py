import os
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset


print(f"Starting Worker with RANK={os.getenv('RANK')}")

try:
    dist.init_process_group(
        backend="nccl",
        init_method="tcp://147.47.122.200:1234",  # 파라미터 서버 주소
        world_size=17,
        rank=int(os.getenv("RANK"))
    )
    print(f"Worker {os.getenv('RANK')} initialized!")

except Exception as e:
    print(f"Error initializing worker: {e}")

# 모델과 데이터 설정
model = nn.Linear(128, 2).cuda()
optimizer = optim.SGD(model.parameters(), lr=0.01)
loss_fn = nn.CrossEntropyLoss()

# 데이터 로더 생성
dataset = TensorDataset(torch.randn(1000, 128), torch.randint(0, 2, (1000,)))
train_loader = DataLoader(dataset, batch_size=16)

model.train()
for epoch in range(1000):
    for batch, target in train_loader:
        optimizer.zero_grad()
        output = model(batch.cuda())
        loss = loss_fn(output, target.cuda())
        loss.backward()

        # 매개변수 동기화
        for param in model.parameters():
            dist.reduce(param.grad.data, dst=0, op=dist.ReduceOp.SUM)
            if dist.get_rank() == 0:
                with torch.no_grad():
                    param.data -= 0.01 * param.grad.data

            # 브로드캐스트 매개변수 업데이트
            dist.broadcast(param.data, src=0)
