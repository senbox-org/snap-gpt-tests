#! /bin/bash

if [[ $# -ne 10 ]]; then
    echo "Illegal number of parameters"
    echo "run_tests.sh SNAP_PARENT_DIRECTORY TEST_SCOPE OUTPUT_DIRECTORY MACHINE_TAG"
    exit 2
fi

SNAP_DIR=$1
SCOPE=$2
ID=`date +%s`
OUTDIR=$3/$ID
TAG=$4
DBCONF=snap-db.conf

echo "Working directory: ${OUTDIR}"
mkdir -p $OUTDIR
echo "Building Output Tester..."
mvn clean install -DskipTests
echo "Filtering tests using scope ${SCOPE}"
python3 pygpt/filter_json.py gpt-tests-resources/tests $SCOPE $OUTDIR
mkdir $OUTDIR/report
echo "Running tests...s"
while read jsonFile; do
    echo "Running ${jsonFile}"
    python3 pygpt/snap_gpt_test.py $SNAP_DIR/jre/bin/java "-Dncsa.hdf.hdflib.HDFLibrary.hdflib=${SNAP_DIR}/snap/modules/lib/amd64/libjhdf.so -Dncsa.hdf.hdf5lib.H5.hdf5lib=${SNAP_DIR}/snap/modules/lib/amd64/libjhdf5.so -cp gpt-tests-executer/target/TestOutput.jar" org.esa.snap.test.TestOutput snap.conf $SCOPE $jsonFile $OUTDIR/report false
done <$OUTDIR/JSONTestFiles.txt
echo "Updating database"
python3 pygpt/stats_db.py $DBCONF $TAG $SCOPE $OUTDIR/report $ID  LOCAL
