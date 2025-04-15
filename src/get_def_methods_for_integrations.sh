cat "$1" |grep "def "|sed '/      def/d'|sed 's/  */ /g' |cut -f2 -d ' '|cut -f1 -d '('
# cat formatting_operations.py |grep "def "|sed '/      def/d'|sed 's/  */ /g' |cut -f2 -d ' '|cut -f1 -d '('
