OUTPUTDIR=$1
TASK=$2
ROUND=$3
TIME=$4"m"
APKID=$5
APKNAME=$APKID".apk"
cd ../6-AppAgent
source activate pytorch
echo $OUTPUTDIR
echo $TASK
echo $ROUND
echo $TIME
echo $APKNAME
if [ ! -f "$OUTPUTDIR" ]; then
	mkdir -p $OUTPUTDIR
fi

adb install ../dataset/apks/$APKNAME
# adb shell monkey -p $APKID -c android.intent.category.LAUNCHER 1
echo timeout $TIME python learn.py --app $APKID -output \"$OUTPUTDIR\" -task \"$TASK\" -round $ROUND
timeout $TIME python learn.py --app $APKID -output "$OUTPUTDIR" -task "$TASK" -round $ROUND
# adb uninstall $APKID