#/bin/bash
docker run -dit --rm --network ps-llama-network \
  --name param-server \
  --hostname param-server \
  -v "$(pwd)":/workspace \
  -w /workspace \
  -e NCCL_DEBUG=INFO \
  -e NCCL_IB_DISABLE=1 \
  -e RANK=0 \
  pytorch/pytorch:latest python3 ./ps/param_server.py

#python3 monitor_containers.py &


## Docker 컨테이너 종료 대기
#docker wait param-server
#
## 컨테이너가 종료되면 모니터링 스크립트도 종료
#pkill -f monitor_containers.py
#echo "Container stopped. Monitoring terminated."

#docker exec -it param-server python param_server.py
