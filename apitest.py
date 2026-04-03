import api
prom='''{{[SYSTEM]}}你是一只电子猫娘。用电子猫娘的语气和用户对话。

{{[INPUT]}}
现在测试通过API和你对话。
{{[OUTPUT]}}
<think>

</think>

'''

for i in api.textcomp_stream(prom):
    print(i,end='')
print()