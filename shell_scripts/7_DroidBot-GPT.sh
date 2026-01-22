OUTPUTDIR=$1
TASK=$2
ROUND=$3
TIME=$4"m"
APKNAME=$5".apk"
cd ../agents/7-DroidBot-GPT
source activate base
echo $OUTPUTDIR
echo $TASK
echo $ROUND
echo $TIME
echo $APKNAME
if [ ! -f "$OUTPUTDIR" ]; then
	mkdir -p $OUTPUTDIR
fi

echo timeout $TIME python start.py -a ../../dataset/apks/$APKNAME -output \"$OUTPUTDIR\" -is_emulator -task \"$TASK\" -round $ROUND -keep_app -keep_env
timeout $TIME python start.py -a ../../dataset/apks/$APKNAME -output "$OUTPUTDIR" -is_emulator -task "$TASK" -round $ROUND -keep_app -keep_env