grep -Eo 'def .*\(' "$1" |sort | uniq -c|grep -v '1'
