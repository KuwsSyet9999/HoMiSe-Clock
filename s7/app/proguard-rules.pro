# 当前未接入第三方库，规则留作后续扩展
# 若反射或序列化相关类被误裁剪，在此补充保留规则

# S7 精简：把类名压到最短包名，进一步缩小 dex 字符串表
-repackageclasses
-allowaccessmodification
