rm cython.log > /dev/null 2> /dev/null
cd ../golismero
find `pwd` -name "*.py" > ../_tmp.txt
cd ../plugins
find `pwd` -name "*.py" >> ../_tmp.txt
cd ../thirdparty_libs/openvas_lib
find `pwd` -name "*.py" >> ../../_tmp.txt
cd ../../tests/plugin_tests
find `pwd` -name "*.py" >> ../../_tmp.txt
cd ../..

find . -name "*.c" -delete > /dev/null 2> /dev/null
find . -name "*.pyc" -delete > /dev/null 2> /dev/null
find . -name "*.pyo" -delete > /dev/null 2> /dev/null

for f in $(cat _tmp.txt);
do
    cython $f >> tests/cython.log
done

rm _tmp.txt
find `pwd` -name "*.c" -delete > /dev/null 2> /dev/null
cd tests
