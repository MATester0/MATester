OUTPUTDIR=$1
TASK=$2
ROUND=$3
TIME=$4"m"
cd ../8-MobileGPT/Server
source activate mobilegpt
echo $OUTPUTDIR
echo $TASK
echo $ROUND
echo $TIME
if [ ! -f "$OUTPUTDIR" ]; then
	mkdir -p $OUTPUTDIR
fi

echo timeout $TIME python main.py -task \"$TASK\" -output \"$OUTPUTDIR\" -round $ROUND
timeout $TIME python main.py -task "$TASK" -output "$OUTPUTDIR" -round $ROUND &
adb install ../App/app/build/outputs/apk/debug/app-debug.apk
wait