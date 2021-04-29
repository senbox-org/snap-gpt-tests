#! /bin/bash

if [[ $# -ne 4 ]]; then
    echo "Illegal number of parameters: ${#}"
    echo "run_tests.sh SNAP_PARENT_DIRECTORY TEST_SCOPE OUTPUT_DIRECTORY MACHINE_TAG"
    exit 2
fi

SNAP_DIR=$1
SCOPE=$2
ID=`date +%s`
OUTDIR=$3/$ID
TAG=`hostname`:$4
DBCONF=conf://snap-db.conf

echo "Working directory: ${OUTDIR}"

mkdir -p $OUTDIR
mkdir -p $OUTDIR/report
mkdir -p $OUTDIR/output

echo "Building Output Tester..."
#mvn clean install -DskipTests
echo "Check test integrity..."
python3 pygpt/check_jsons.py gpt-tests-resources/tests
echo "Filtering tests using scope ${SCOPE}"
python3 pygpt/filter_json.py gpt-tests-resources/tests $SCOPE $OUTDIR
# add empty last line to make sure to execute all tests
echo "" >> $OUTDIR/JSONTestFiles.txt
echo "Running tests..."
cat $OUTDIR/JSONTestFiles.txt | while read jsonFile
do
    echo "Running ${jsonFile}"
    python3 pygpt/snap_gpt_test.py java "-Dncsa.hdf.hdflib.HDFLibrary.hdflib=${SNAP_DIR}/snap/modules/lib/amd64/libjhdf.so -Dncsa.hdf.hdf5lib.H5.hdf5lib=${SNAP_DIR}/snap/modules/lib/amd64/libjhdf5.so -cp gpt-tests-executer/target/TestOutput.jar" org.esa.snap.test.TestOutput snap.conf $SCOPE $jsonFile $OUTDIR/output true
done
mv $OUTDIR/output $OUTDIR/report/output
cat $OUTDIR/report/output/Report_*.txt > $OUTDIR/report/output/report.txt
mv $OUTDIR/report/output/json $OUTDIR/report/ && mv $OUTDIR/report/output/performances $OUTDIR/report/ && mv $OUTDIR/report/output/images $OUTDIR/report/
cp -R pygpt/statics/* $OUTDIR/report/

echo "Generate report"
python3 pygpt/report_utils.py pygpt/templates $OUTDIR/report $SCOPE snap:8.x $DBCONF
# echo "Updating database"
# python3 pygpt/stats_db.py $DBCONF $TAG $SCOPE $OUTDIR/report $ID snap:8.x

