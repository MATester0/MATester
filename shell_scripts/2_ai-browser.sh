OUTPUTDIR=$1
TASK=$2
ROUND=$3
TIME=$4"m"
cd ../2_ai-browser/ai-browser
echo $OUTPUTDIR
echo $TASK
echo $ROUND
echo $TIME
if [ ! -f "$OUTPUTDIR" ]; then
	mkdir -p $OUTPUTDIR
fi
echo timeout $TIME npm run start \"output=$OUTPUTDIR\" \"task=$TASK\" \"round=$ROUND\"
timeout $TIME npm run start \'output=$OUTPUTDIR\' \'task=\"$TASK\"\' \'round=$ROUND\'
