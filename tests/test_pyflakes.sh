rm pyflakes-out.log pyflakes-err.log > /dev/null 2> /dev/null
cd ../golismero
find `pwd` -name "*.py" > ../_tmp.txt
cd ../plugins
find `pwd` -name "*.py" >> ../_tmp.txt
cd ../thirdparty_libs/openvas_lib
find `pwd` -name "*.py" >> ../../_tmp.txt
cd ../..
find . -name "*.pyc" -delete > /dev/null 2> /dev/null
find . -name "*.pyo" -delete > /dev/null 2> /dev/null

for f in $(cat _tmp.txt);
do
    pyflakes $f >> tests/pyflakes-out.log 2>> tests/pyflakes-err.log
done

rm _tmp.txt
cd tests