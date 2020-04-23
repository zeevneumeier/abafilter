echo "running abafilter"


/usr/local/bin/python3 /Users/zeev/workspace/abafilter/abafilter.py /Users/zeev/workspace/abafilter/ 1c1wIVkNGuluoVmBTPuMH3FKdFnbmJ6i3JDcb8jY7wU8 60 300

/usr/local/bin/python3 /Users/zeev/workspace/abafilter/logsaver.py /Users/zeev/workspace/abafilter/ /tmp/abafilter.out test

echo "" > /tmp/abafilter.out

/usr/local/bin/python3 /Users/zeev/workspace/abafilter/logsaver.py /Users/zeev/workspace/abafilter/ /tmp/abafilter.err test

echo "" > /tmp/abafilter.err

