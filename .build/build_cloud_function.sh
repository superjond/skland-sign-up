# 构建云函数,必须使用linux编译
cd ../
pyinstaller --distpath ./dist/cloud_functions -F index.py
mkdir dist/cloud_functions
touch dist/cloud_functions/INPUT_HYPERGRYPH_TOKEN.txt
echo "./index" > bootstrap