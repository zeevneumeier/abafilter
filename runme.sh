
echo "updating code"

git -C /usr/local/abafilter pull

echo $PATH
export PATH=$PATH:/usr/local/bin/

echo "running abafilter"

/usr/local/bin/python3 /usr/local/abafilter/abafilter.py /usr/local/abafilter 1c1wIVkNGuluoVmBTPuMH3FKdFnbmJ6i3JDcb8jY7wU8 300 43200

echo "uploading logs"

/usr/local/bin/python3 /Users/zeev/workspace/abafilter/logsaver.py /Users/zeev/workspace/abafilter/ /tmp/abafilter.out test

echo "" > /tmp/abafilter.out

/usr/local/bin/python3 /Users/zeev/workspace/abafilter/logsaver.py /Users/zeev/workspace/abafilter/ /tmp/abafilter.err test

echo "" > /tmp/abafilter.err
