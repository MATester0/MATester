OUTPUTDIR=$1
TASK=$2
ROUND=$3
TIME=$4"m"
cd ../agents/6-MC-Planner
source activate planner
echo $OUTPUTDIR
echo $ROUND
echo $TIME
if [ ! -f "$OUTPUTDIR" ]; then
	mkdir -p $OUTPUTDIR
fi

echo timeout $TIME python main.py model.load_ckpt_path=../../../checkpoints/controller.pt eval.output=\"$OUTPUTDIR\" eval.task_name=\"$TASK\" eval.round=$ROUND
timeout $TIME python main.py model.load_ckpt_path=../../../checkpoints/controller.pt eval.output="$OUTPUTDIR" eval.task_name="$TASK" eval.round=$ROUND