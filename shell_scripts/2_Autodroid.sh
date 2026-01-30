OUTPUTDIR=$1
TASK=$2
ROUND=$3
TIME=$4"m"
APKNAME=$5".apk"
cd ../agents/2-AutoDroid/AutoDroid
source activate base
echo $OUTPUTDIR
echo $TASK
echo $ROUND
echo $TIME
echo $APKNAME
if [ ! -f "$OUTPUTDIR" ]; then
	mkdir -p $OUTPUTDIR
fi
echo timeout $TIME python start.py  -a ../../../dataset/apks/$APKNAME -output \"$OUTPUTDIR\" -is_emulator -task \"$TASK\" -round $ROUND -keep_env -keep_app
timeout $TIME python start.py -a ../../../dataset/apks/$APKNAME -output "$OUTPUTDIR" -is_emulator -task "$TASK" -round $ROUND -keep_env -keep_app
