import dashscope
from dashscope.audio.tts_v2 import *

# 若没有将API Key配置到环境变量中，需将下面这行代码注释放开，并将apiKey替换为自己的API Key
# dashscope.api_key = "apiKey"
model = "cosyvoice-v1"
voice = "longxiaochun"
text='''
在这个快速变化的季节，如何让自己在人群中脱颖而出？答案就是选对衣服！我们最新推出的秋冬系列，完美结合时尚与舒适，让你无论是出门工作，还是周末聚会，都能轻松驾驭每个场合。

**时尚设计，展现独特魅力**
每一件衣服都经过精心设计，采用优质面料，打破了传统的单调设计，加入了更多现代元素。无论是简洁大气的外套，还是别致的毛衣，都能为你的穿搭增添无限魅力。独特的剪裁让你完美展现身形，贴合每个人的个性和风格。

**舒适与温暖并存**
我们深知舒适感对于衣物的重要性。精选的羊毛、棉麻等材质，柔软亲肤，极富弹性，不仅让你感受到温暖，还能确保全天候的舒适穿着体验。无论是寒冷的早晨，还是寒风刺骨的傍晚，这款衣服都能带给你满满的温暖感。

**百搭款式，轻松搭配**
“穿搭难？”不再是问题！我们的衣服设计简洁大方，色彩也以经典为主流，轻松搭配任何裤子或裙子。你可以将它们与牛仔裤搭配，打造休闲风；或者配上优雅的半裙，轻松拥有时尚感十足的淑女风格。穿上它，不管走到哪里，都会吸引无数目光。

**品质保证，细节之处见真章**
每一件衣服都是我们用心打造的精品。精细的缝线，精选的钮扣和拉链，让你穿得放心，买得安心。我们的质量控制严格把关，确保每一件衣服都经得起时间的考验，无论是颜色的持久，还是布料的耐用性，都能给你带来超高的使用价值。

**让每一刻都充满自信**
穿上这款衣服，展现不一样的自己。无论是走在街头，还是参加聚会，你都会成为焦点。让我们帮助你找到适合自己的风格，展现你的个人魅力，走出属于你的精彩人生。

快来选择你心仪的款式，让这个季节的每一天都充满自信与温暖吧！


'''
synthesizer = SpeechSynthesizer(model=model, voice=voice)
audio = synthesizer.call(text)
print('requestId: ', synthesizer.get_last_request_id())
with open('output.mp3', 'wb') as f:
    f.write(audio)