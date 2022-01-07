from scipy.spatial.distance import euclidean
import numpy as np
import imutils
import time
import cv2

'''
来自于：Lya
（from：Lya）
大四在学校太无聊做的 
（I did it in college because I was bored）
'''


def delay(content):
    print('--------' + str(content) + '--------')
    time.sleep(0.5)


def set_camera_type():
    delay('设置相机调用')
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
                delay('选择：内置摄像头')
            else:
                delay('选择：外置摄像头')
            break
    return set_type


def call_camera():
    camera = cv2.VideoCapture(camera_type, cv2.CAP_DSHOW)  # 创建摄像头对象
    if camera.isOpened() is False:
        delay('摄像头调用失败')
        raise AssertionError
    else:
        delay('摄像头调用成功')
        delay('正在选择参照物，按下回车确认选择')
        while True:
            frame = camera.read()[1]  # 返回捕获到的RGB
            image = cv2.flip(frame, 1, dst=None)  # 镜像
            cv2.imshow('Camera', image)  # 创建窗口
            if (cv2.waitKey(1) > -1) or (cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE) < 1.0):  # 设置关闭条件
                cv2.destroyWindow('Camera')  # 关闭窗口
                break
    return image


def get_points(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 二值化
    gaussian_blur = cv2.GaussianBlur(gray_image, (5, 5), 0)  # 高斯模糊
    min_val, max_val = 50, 100
    margin = cv2.Canny(gaussian_blur, min_val, max_val)  # 边沿检测
    open_margin = cv2.dilate(margin, None, iterations=15)  # 开运算
    contours = cv2.findContours(open_margin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 查找所有轮廓
    points = imutils.grab_contours(contours)  # 返回所有路径的端点
    return points


def reference_processing():
    circulation = True
    while circulation:  # 选择轮廓
        image = call_camera()  # 调用摄像头
        points = get_points(image)  # 图像处理
        selected_points = []  # 创建被筛选的轮廓数据的容器

        # --------按面积大小筛选轮廓--------
        filter_area = 1
        while True:
            [selected_points.append(i) for i in points if cv2.contourArea(i) > filter_area]  # 筛选后的端点
            if len(selected_points) > 1:
                selected_points.clear()  # 清空内容，为下一次存储数据用
                filter_area += 1  # 自筛选，可以筛选掉毛刺
            else:
                break
        reference_area_point = draw_frame(image, selected_points, 0)
        while True:
            cv2.imshow('reference', image)  # 创建窗口
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


def rate_calculation():
    delay('计算比率')
    left_point, right_point = reference_points[0], reference_points[1]  # 获取最左侧点与最右侧点坐标
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


def draw_frame(image, points, tag):
    if tag == 0:
        for point in points:
            min_area = cv2.minAreaRect(point)  # 计算最小外接矩阵面积
            min_area_point = cv2.boxPoints(min_area)  # 获取最小外接矩阵的四个端点
            # perspective_point = perspective.order_points(min_area_point)  # 端点透视变换
            int_point = [min_area_point.astype('int')]  # 修改数据类型
            # int_point = [perspective_point.astype('int')]  # 修改数据类型
            cv2.drawContours(image, int_point, -1, (0, 0, 255), 1)
            return min_area_point
    else:
        for point in points:
            min_area = cv2.minAreaRect(point)  # 计算最小外接矩阵面积
            min_area_point = cv2.boxPoints(min_area)  # 获取最小外接矩阵的四个端点
            left_point, right_point = min_area_point[0], min_area_point[1]  # 获取两处端点的信息
            X = left_point[0] + int(abs(right_point[0] - left_point[0]) / 2)  # 获取顶部中点X坐标
            Y = left_point[1] + int(abs(right_point[1] - left_point[1]) / 2)  # 获取顶部中点Y坐标
            int_point = [min_area_point.astype('int')]  # 修改数据类型
            cv2.drawContours(image, int_point, -1, (0, 0, 255), 1)  # 绘制边框
            radius = (euclidean(left_point, right_point) / 2) / rate  # 获取半径
            area = int((3.1415926 * pow(radius, 2)))  # 面积计算(圆)
            # 展示面积信息
            cv2.putText(image, '{}'.format(area), (int(X), int(Y)), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 5)


def real_time_processing():
    delay('进入实时测量，按下回车键结束程序')
    camera = cv2.VideoCapture(camera_type, cv2.CAP_DSHOW)  # 创建摄像头对象
    while True:
        frame = camera.read()[1]  # 返回捕获到的RGB
        image = cv2.flip(frame, 1, dst=None)  # 镜像
        points = get_points(image)  # 获取所有参照物的端点
        selected_points = []
        [selected_points.append(i) for i in points if cv2.contourArea(i) > filter_area]  # 筛选后的端点
        draw_frame(image, selected_points, 1)  # 绘制边框
        cv2.imshow('Camera', image)  # 创建窗口
        if (cv2.waitKey(1) > -1) or (cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE) < 1.0):  # 设置关闭条件
            cv2.destroyWindow('Camera')  # 关闭窗口
            break


if __name__ == '__main__':
    t1 = time.time()
    camera_type = set_camera_type()  # 设置相机类型
    filter_area, reference_points = reference_processing()  # 创建被过滤面积值
    rate = rate_calculation()  # 计算欧氏距离与实际距离的比率
    real_time_processing()  # 实现实时测量
    t2 = time.time()
    delay('程序结束，共运行{}秒'.format(t2 - t1))
