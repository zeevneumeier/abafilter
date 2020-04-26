
echo "updating code"

git -C /usr/local/abafilter pull

echo $PATH
export PATH=$PATH:/usr/local/bin/

NAME="test"
SHEET="c1wIVkNGuluoVmBTPuMH3FKdFnbmJ6i3JDcb8jY7wU8"

echo "running abafilter"

python3 /usr/local/abafilter/abafilter.py /usr/local/abafilter $SHEET 300 43200

echo "uploading logs"

python3 /usr/local/abafilter/logsaver.py /usr/local/abafilter/ /tmp/abafilter.out $NAME

echo "" > /tmp/abafilter.out

python3 /usr/local/abafilter/logsaver.py /usr/local/abafilter/ /tmp/abafilter.err $NAME

echo "" > /tmp/abafilter.err
