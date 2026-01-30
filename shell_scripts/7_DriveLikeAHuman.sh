OUTPUTDIR=$1
ROUND=$2
TIME=$3"m"
cd ../agents/7-DriveLikeAHuman
source activate gptdriver
echo $OUTPUTDIR
echo $ROUND
echo $TIME
if [ ! -f "$OUTPUTDIR" ]; then
	mkdir -p $OUTPUTDIR
fi

echo timeout $TIME python HELLM.py -output \"$OUTPUTDIR\" -round $ROUND
timeout $TIME python HELLM.py -output "$OUTPUTDIR" -round $ROUND