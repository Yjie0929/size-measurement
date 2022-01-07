# Hey~ 

# 前言
**注意：不讲实现原理，也没有做UI，精度就玩玩的级别，记得打（尽量柔和的）光。**
# for reference only. 
# for learning.
# （仅供参考，只用于学习）

(Because I'm still a student, there are many things I don't understand or easily make mistakes, so, I'm sooooorry.)

这里做个简要说明：

    选择pycharm还是Anaconda或是其它都可以;
    工作平台尽量使用纯色;
    工作时一定要尽量为被检测对象打上柔和的光照，否则会被拾取到影子;
    相机的高度尽量保持不变，相机高度发生变化会导致出现误差;
    被检测对象以圆型为主;
    计算距离的方式是将两点的欧式距离求出后，比上比率;

实现方式：

    1、使用相机对参照物拍照，先将被捕获的图像二值化、高斯滤波，再经过边缘检测、开运算(1.1)、拾取轮廓；
       1.1：（开运算的iterations次数为15，这是因为我没有纯色平台作为背景，只能采用多次膨胀的方式防止边缘不连续）
       
    2、第1步获取轮廓数据后需要计算最小外接矩阵面积，之后再获取这个面积的四个端点坐标用于绘制方框；
    
    3、为了能够有效地拾取(3.1)参照物，必须采用手动确认的方式保证(3.2)选取到的参照物没问题、边框绘制也没问题；
       3.1：（在拾取参照物的过程中常会捕捉到一些不必要的信息，所以需要通过筛选保证只能获取到参照物的数据）
       3.2：（手动确认是一个循环过程，如果选取错了或没框选好，那么就需要手动进入循环，再次拍照 -> 框选 -> 确认）
       
    4、边框的两个终点（极左、极右）坐标用来计算欧氏距离(4.1)，完成计算后手动测量参照物的对应尺寸即可计算比率(4.2)
       4.1：（euclidean是OpenCV常用的度量方式之一，除此之外还有cosine、minkowski、haversine等许多度量方式）
       4.2：（比率是欧式距离除以真实距离得出的比值，假设被捕获到的物体欧式距离为100，那么真实距离 = 100/比值）
       
    5、在比率已经成功获取之后就只需要做循环计算的工作了:
       简单来说就是：循环(拍照 -> 计算绘制边框数据 -> 计算被测量对象数据 -> 绘制边框 -> 绘制数据)


博主是一名机械设计制造及其自动化专业的学生，以前在车间上课时总需要挑选特定尺寸的毛坯作为被加工工件，奈何本人较懒，所以就有了码这么一个py文件出来助我偷懒的想法。

<div align=center><img src="https://user-images.githubusercontent.com/83082953/148507103-6ac3a952-3759-47e6-9293-91cfa23fe614.jpg"></div>



## 一、开发前准备
**喜欢用Pycharm还是Anaconda或其它都可以，没有关系。**
因为摄像头使用的只是普通的家用摄像头（某夕个位数包邮），所以在码程序之前需要准备一个尺寸精度较高（尽量高）的参照物来获取欧氏距离和真实长度的比率。

**穷得只能3D打印的屑博主：10mm³，20mm³，30mm³**

<div align=center><img src="https://user-images.githubusercontent.com/83082953/148508807-70604663-6966-422c-b188-8b4d8f1f3142.jpg" width="640" height="460" /></div>


## 二、需要的库
```python
from scipy.spatial.distance import euclidean  # 用来计算端点之间的欧氏距离
import numpy as np
import imutils
import time
import cv2
```


## 三、程序主体

### 3.1设置被调用的摄像头类型
这段函数是为了方便程序能够在内置相机或外置相机之间来回切换工作。如果有外置相机或确定仅使用外置相机的情况下可以忽略这一步，在调用相机时将调用相机类型设置为1便可。
```python
def set_camera_type():
    while True:
        try:
            set_type = int(input('摄像头调用（输入数字代号：0.内置，1.外置）：'))
        except ValueError:
            delay('输入参数类型错误')
            continue
        else:
            if (set_type < 0) or (set_type > 1):
                delay('输出参数不在范围内')
                continue
            elif set_type == 0:
                print('选择：内置摄像头')
            else:
                print('选择：外置摄像头')
            break
    return set_type
```

### 3.2调用相机

 如确认仅使用外置相机时将camera_type设置为‘1’，cv2.CAP_DSHOW为可选参数，在相机调用过程中出现不知名报错时试着加入。
 - .isOpened()返回一个布尔值，在相机调用失败后会返回False
 - cv2.flip()可以将图像（RGB）镜像：1=水平镜像，0=垂直镜像，-1=对角（水平垂直）镜像

但如果遇到cv2.imshow的窗口关闭了但又没有完全关闭的情况很容易导致堵塞，所以需要判断窗口是否被关闭后使用命令再次关闭。**可以忽略，但后期想要引入多线程这一步极其重要。**
 - cv2.getWindowProperty()能够检测到指定窗口是否被关闭，详细用法可以查看源码
 - cv2.destroyWindow()用于关闭窗口

```python
def call_camera():
    camera = cv2.VideoCapture(camera_type, cv2.CAP_DSHOW)  # 创建cv2.VideoCapture对象
    if camera.isOpened() is False:
        print('摄像头调用失败')
        raise AssertionError  # 调用失败则断言停止
    else:
        while True:
            frame = camera.read()[1]  # 返回捕获到的RGB
            image = cv2.flip(frame, 1, dst=None)  # 图片镜像
            cv2.imshow('Camera', image) 
            if (cv2.waitKey(1) > -1) or (cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE) < 1.0):  # 设置关闭条件
                cv2.destroyWindow('Camera')  # 关闭窗口
                break
    return image

```
### 3.3图像处理（轮廓端点查找）
简单的说，cv2.Canny中的min_val与max_val参数值的大小可以判断是否为边，且**值越小，拾取到的边缘信息就越多**。为了方便，我把获取轮廓信息的步骤直接放在图像处理的后一步，如果逻辑能力强且记性好的话建议单独define。

 - **cv2.findContours**有2个返回值，分别是contours和hierarchy，前者是被检测到的轮廓信息，后者意义不明。函数**用于检测物体的轮廓**，**cv2.RETR_EXTERNAL**表示只检测边缘信息的外轮廓，**cv2.CHAIN_APPROX_SIMPLE**表示只用四个端点坐标表示轮廓信息。
 - **imutils.grab_contours**用来获取**cv2.findContours**的contours，**cv2.findContours**的contours才是实际上能够被用于计算的数据。
```python
def get_points(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 二值化
    gaussian_blur = cv2.GaussianBlur(gray_image, (5, 5), 0)  # 高斯平滑
    min_val, max_val = 50, 100
    margin = cv2.Canny(gaussian_blur, min_val, max_val)  # 边缘检测
    open_margin = cv2.dilate(margin, None, iterations=15)  # 开运算，如果有纯色平台iteration可以小一些
    contours = cv2.findContours(open_margin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 轮廓查找
    points = imutils.grab_contours(contours)   # 获取轮廓数据
    return points
```
### 3.4边框绘制（数据计算）
这一部分程序的用处主要是绘制框架与数据计算。程序前期在对参照物对象拍照时需要绘制框架呈现出被选中的对像，在程序后期除了要绘制框架外，还要通过比率计算真实长度、面积，最后在绘制框架的同时把计算结果也显示出来。
```python
def draw_frame(image, points, tag):
    if tag == 0:
        for point in points:
            min_area = cv2.minAreaRect(point)  # 计算最小外接矩阵面积
            min_area_point = cv2.boxPoints(min_area)  # 获取最小外接矩阵的四个端点
            int_point = [min_area_point.astype('int')]  # 修改为cv2.drawContours能够读取的数据类型
            cv2.drawContours(image, int_point, -1, (0, 0, 255), 1)  # 点连线绘制
            return min_area_point
    else:
        for point in points:
            min_area = cv2.minAreaRect(point)   # 计算最小外接矩阵面积
            min_area_point = cv2.boxPoints(min_area)  # 获取最小外接矩阵的四个端点
            left_point, right_point = min_area_point[0], min_area_point[1]  # 获取左上、右上的两个端点，用于计算长度
            X = left_point[0] + int(abs(right_point[0] - left_point[0]) / 2)  # 获取顶部中点X坐标，用于定位文字显示位置x
            Y = left_point[1] + int(abs(right_point[1] - left_point[1]) / 2)  # 获取顶部中点Y坐标，用于定位文字显示位置y
            int_point = [min_area_point.astype('int')]
            cv2.drawContours(image, int_point, -1, (0, 0, 255), 1)  # 绘制边框
            radius = (euclidean(left_point, right_point) / 2) / rate  # 获取半径
            area = int((3.1415926 * pow(radius, 2)))   # 将被测量物体视为圆，套入计算公式
            # 展示面积信息
            cv2.putText(image, '{}'.format(area), (int(X), int(Y)), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 5)
```
我的检测对象一般以圆形为主，所以只需要取出最左、最右的两个点坐标就能够用于计算了
```python
min_area_point = cv2.boxPoints(min_area)  # 获取最小外接矩阵的四个端点
left_point, right_point = min_area_point[0], min_area_point[1]  # 获取两处端点的信息
```
### 3.5比率计算
比率是参照物两点在度量空间内两点距离和真实距离的比值，本项目后期所有的计算尺寸均由欧氏距离比上比率得出。如点1与点2在空间内长度为400，而参照物在测量后的实际距离为20，那么比率为400/20=20。比率计算完成后存入容器中，假设下一个被测量物体上两点的空间距离为510，那么实际长度=510/20。
```python
def rate_calculation():
    delay('计算比率')
    left_point, right_point = reference_points[0], reference_points[1]  # 获取极左、极右两点，用于计算度量空间内的距离
    length_euclidean = euclidean(left_point, right_point)  # 计算欧氏距离
    while True:
        try:
            length_reference = int(input('输入参照物长度(mm)：'))
        except ValueError:
            delay('输入参数类型错误')
            continue
        else:
            if length_reference <= 0:
                delay('参数不可小于或等于0')
                continue
            else:
                break
    rate = length_euclidean / length_reference  # 比率计算
    print('(参照物)欧氏长度：{}mm'.format(length_euclidean))
    print('(参照物)实际长度：{}mm'.format(length_reference))
    print('长度比率：{}'.format(rate))
    return rate
```
### 3.6参照物选取（拍照）
在调试过程中有多次遇到过拍照后参照物选取不正确，为了防止这一情况的出现就设置了while循环，只有在手动确认参照物被正常框选的情况下才能进入下一步。
值得关注的是selected_points 的筛选方式，在没有纯黑或其它纯色的平台上放置物体很容易捕获到许多不需要的信息，尤其是在有许多**小的坑坑洼洼**的桌子上，所以就采用了将筛选面积不断加一，直到只剩下参照物对象的方式，即len(selected_points) = 1。
```python
def reference_processing():
    circulation = True  # 设置循环条件
    while circulation:
        image = call_camera()
        points = get_points(image)  # 图像处理
        selected_points = []  # 创建被筛选的轮廓数据的容器
        # --------按面积大小筛选轮廓--------
        filter_area = 1  # 设置最初筛选值
        while True:
            [selected_points.append(i) for i in points if cv2.contourArea(i) > filter_area]
            if len(selected_points) > 1:
                selected_points.clear()  # 清空内容，为下一次存储数据用
                filter_area += 1  # 筛选面积+1
            else:
                break
        reference_area_point = draw_frame(image, selected_points, 0)  # 调用draw_frame绘制边框
        while True:
            cv2.imshow('reference', image)  # 窗口显示
            if (cv2.waitKey(1) > -1) or (cv2.getWindowProperty('reference', cv2.WND_PROP_VISIBLE) < 1.0):  # 设置关闭条件
                cv2.destroyWindow('reference')  # 关闭窗口
                break
        while circulation:
            try:
                tag = str(input('是否是理想参照物(Y/N)：'))
            except ValueError:
                delay('输入参数类型错误')
                continue
            else:
                if (tag == 'Y') or (tag == 'y'):
                    circulation = False
                    break
                elif (tag == 'N') or (tag == 'n'):
                    break
    return filter_area, reference_area_point

```
### 3.7实时测量
这段就不多说了，和前面基本一样的原理。
```python
def real_time_processing():
    print('进入实时测量，按下回车键结束程序')
    camera = cv2.VideoCapture(camera_type, cv2.CAP_DSHOW)
    while True:
        frame = camera.read()[1]  # 返回捕获到的RGB
        image = cv2.flip(frame, 1, dst=None)  # 水平镜像
        points = get_points(image)  # 获取所有参照物的端点
        selected_points = []
        [selected_points.append(i) for i in points if cv2.contourArea(i) > filter_area]  # 筛选后的端点
        draw_frame(image, selected_points, 1)  # 绘制边框
        cv2.imshow('Camera', image) 
        if (cv2.waitKey(1) > -1) or (cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE) < 1.0):
            cv2.destroyWindow('Camera') 
            break

```
## 四、成果展示
**执行过程：**（不小心多摁了一次enter，所以是否理想参照物又被循环输出了一次）

<div align=center><img src="https://github.com/Yjie0929/object-size-measurement-based-on-OpenCV/blob/f9681ea5d156d4b98ff1541263a260b046419f96/%E6%89%A7%E8%A1%8C%E8%BF%87%E7%A8%8B.png"></div>


**参照物拍照：**（指方为圆）

<div align=center><img src="https://github.com/Yjie0929/object-size-measurement-based-on-OpenCV/blob/f9681ea5d156d4b98ff1541263a260b046419f96/%E5%8F%82%E7%85%A7%E7%89%A9.png" width="640" height="460" /></div>

**实时测量：**（指方为圆），这里摄像头高度发生了变化，拍摄角度也出现误差，可以采用只存储最小值数据尽量保证精度。

<div align=center><img src="https://github.com/Yjie0929/object-size-measurement-based-on-OpenCV/blob/f9681ea5d156d4b98ff1541263a260b046419f96/%E7%BB%93%E6%9E%9C.png" width="640" height="460" /></div>

**验证：**（高度发生变化出现的误差为-4）

<div align=center><img src="https://github.com/Yjie0929/object-size-measurement-based-on-OpenCV/blob/45801db4c06e468f9cac16c4e5dc36e30cf50030/%E9%AA%8C%E8%AF%81%E5%85%AC%E5%BC%8F.png"></div>


**补充：测量出现误差的主要原因在这！累死我了，有钱以后我一定要买一个摄像头！！**

<div align=center><img src="https://github.com/Yjie0929/object-size-measurement-based-on-OpenCV/blob/45801db4c06e468f9cac16c4e5dc36e30cf50030/%E7%B4%AF%E6%AD%BB%E6%88%91%E4%BA%86.png" width="640" height="460" /></div>
