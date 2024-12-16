for i in {0..3}; do
  echo $((i+1));
  docker run -dit --rm --network ps-llama-network \
    --name worker-1-gpu-$i \
    --hostname worker-1-gpu-$i \
    --gpus '"device='$i'"' \
    -v "$(pwd)":/workspace \
    -w /workspace \
    -e NCCL_DEBUG=INFO \
    -e NCCL_IB_DISABLE=1 \
    -e RANK=$((i+1)) \
    pytorch/pytorch:latest python3 ./workers/worker.py
done
#
#python3 monitor_containers.py &
#
## Docker 컨테이너 종료 대기
#docker wait worker-1-gpu-3
#
## 컨테이너가 종료되면 모니터링 스크립트도 종료
#pkill -f monitor_containers.py
#echo "Container stopped. Monitoring terminated."
