# Guluton
Guluton是一个基于go-cqhttp开发的qq机器人，具体功能参见文档

【待填坑】
1、自动读取管理员qq号和qq机器人qq号
2、自动启动go-cqhttp
3、群聊管理系统：用于判断哪些群是会进行交互的
4、事件系统：自动读取已经配置的事件时间，并在指定时间提示指定用户

【注意事项】
本程序基于go-cqhttp接口编写，通过web-socket接受信息，并在api上传信息，因此需要配置好go-cqhttp的websocket端口为5701，http端口5700

自行在源码修改qq号，你大概需要修改管理员qq号以及机器人qq号
需要创建dict文件夹，用于存放匹配字典
字典格式参照song.txt
需要创建cookie文件夹，方便爬取网易云音乐时所需的登录事项
使用了python3.8进行开发，需要自行添加python库

【开发log】

//时间：刚写完这个文档2022年10月3日13点44分
	貌似所有能想到的功能都是基于时间提醒助手的呢，决定先把时间提醒助手写好，然后再写时间提醒助手的插件
	又想到可以搞点屏蔽词一类的功能，先搁置
	我看网上有内些通过api查询某某信息的功能，个人觉得呃这一类功能太专一了，兼容性一般
	不过想到可以搞一个”来点二次元“功能，自动搜索图床，爬取api调用方式，然后得到二次元图片并发送，也是极好的，先搁置

//时间：2022年10月3日13点53分
	欸嘿感觉仪表盘功能简单一点，先写这个

//时间：2022年10月3日17点09分
	闹钟这个功能貌似得学会多线程呢。。。只能先拿单线程写了

//时间：2022年10月4日14点58分
	实现了呃实现了一大堆模块
	监听socket接收消息
	处理消息类型分发给各自handler
	识别关键词并回复

//时间：2022年10月4日21点50分
	已经实现部分群组交互功能（播放说的道理和古神语自动翻译）
	计划一会儿搞一个管理员录入字典功能
	计划明天搞一下基于时间的控制器

//时间：2022年10月4日22点02分
	令牌系统好像有些累赘，决定取消掉，改为识别QQ号
	录入a字典功能貌似需要读写本地文件，再琢磨琢磨

//时间：2022年10月5日09点20分
	昨晚忘记写了，现在支持了一键读取本地字典功能，而且可以远程重载，字典为json格式（大概），里面有两项必须存在的消息头和消息尾，用来对字典中存在的键返回对应的值，后期应该会基于时间系统做一些不会大量重复的字典类型，否则大家都在复读机的时候机器人也说一句复读一句有点呆。。。 今天先摆一天，写写作业

//时间：2022年10月10日20点38分
	我差点忘了还有日志这个东西，现在在开发自动爬取用户网易云音乐听歌排行并返回，边学边写，漫漫长路啊

//时间：2022年10月10日23点27分
	通过不懈的努力调试，成功实现了该功能看好了，WebDriverWait是这样用的，鳖jb惦记着你内个破b time.sleep了。我真是卡在这个地方调试的要死了，结果是没加WebDriverWait哎哟心累，下面只需要把返回的列表进行一个输出就行了

	参考了一篇http://t.zoukankan.com/martinsun-p-15512048.html
	一直在研究对于抛出异常的处理，发现根本没法处理到底是超时还是没内容，只能嵌套一下看有没有内容从而判断给没给权限（？）
	我改变主意了，既然能switch to frame说明网页加载肯定是成功了那么如果没有这个元素一定是没权限我简直是天才哈哈哈哈
	哦还有，报错我没用WebDriverWait的message因为我觉得影响阅读

//时间：2022年10月11日11点07分
	机器人试运行，稍微改了点bug
	预备新增爬取用户动态随机内容、搜索并播放第一首

//时间：2022年10月11日20点47分
	从外面回来力，搜索功能也搞好了，明天搞完爬动态就等于填完坑了
	然后开始搞事件功能
	
//时间：2022年10月16日12点29分
	爬网易云音乐动态计划暂缓，感觉效果一般，摆烂了五天(⊙﹏⊙)
	今天正式开始写事件功能，先搞好群组分组功能然后搞事件

//时间：2022年10月16日21点43分
	我真是吐了为什么在写入文件的时候会拒绝访问啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊
	闹钟功能仍然未完成，群组分组功能可用，但不能在程序段增删groups.txt，哎哟我真的是服了到底是什么bug
	
//时间：2022年10月17日14点34分
	听从了大哥的建议决定重构代码，之前的bug貌似是忘记写文件地址了。。。。。。

//时间：2022年10月17日15点32分
	把硬编码换成了config载入，可以编辑config.json配置文件更加方便地使用。全面将txt更换为json文件，易于阅读和编辑

//时间：2022年10月18日00点14分
	闹钟系统的生成，读写，增删等等已经写完，待测试
	睡前构思一下如何录入一个闹钟
	群聊内：@Guluton 闹钟 17:00(:30) 每周1,2,3/每2天 (小睡100 200 300) (速速起床 某某图片)
感觉暂时只能管理员用比较好
	私聊不用@
	感觉明天又是正则的一天哎哟

//时间：2022年10月18日19点40分
	想要支持发送图片等闹钟消息，复杂度增加了

//时间：2022年10月19日10点50分
	闹钟功能调试完毕，后续相关补充功能会逐步添加
	貌似发图片也不是很难
	哦对了查询闹钟需要优化一下，挖坑

//时间：2022年10月19日17点03分
	查询闹钟先这样，下一步将字典匹配和闹钟结合起来，为字典匹配设置一个冷却参数，防止重复匹配刷屏
	还要把全员核酸自动广播搞一下

//时间：2022年10月19日23点48分
	发现漏洞：可能会影响程序功能
		小睡功能直接使用数字运算，待处理

//时间：2022年10月20日11点32分
	感觉不止需要groups.json还需要users.json，或者整合两者，整合好一点吧，但是这样的话需要改一下代码

//时间：2022年10月20日16点52分
	把储存时间改为了list并且一旦读取就转换为datetime类型，解决了增减时间漏洞，增加了超时闹钟未响反馈
	render功能做好了，可以编辑time_table设置

#时间：2022年10月23日22点28分-------end？

说的道理的自动撤回也已经完善，字典匹配也许需要增加一个冷却功能防止频繁复读

Guluton的制作告一段落，现在我的水平很低，所以代码等等绕了很多弯路，也有很多不规范，以后可能不会这么写而是转向框架了。代码先这样，日后若是有需要也许可能考虑部署在服务器，日后再说了~
