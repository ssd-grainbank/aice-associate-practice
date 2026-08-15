#!/bin/zsh
# 더블클릭하면 시험 세트 목록이 열립니다.
cd "$(dirname "$0")"
clear
python3 exam.py
echo ""
echo "  세트를 고르려면 아래처럼 치세요:"
echo "     aice 1      (1세트 풀기)"
echo "     aice 1 -a   (정답 보며 따라치기)"
echo ""
exec $SHELL
