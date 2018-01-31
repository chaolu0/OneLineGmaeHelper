from jpype import *
import os
import time
from PIL import Image

'''
通过shell命令，截图、上传、打开
return Image，w,h
'''


def get_photo():
    os.system('adb shell screencap -p /sdcard/oneline.png')
    os.system('adb pull /sdcard/oneline.png .')
    img = Image.open('oneline.png')
    w, h = img.size
    return img, w, h


'''
寻找关键坐标
start_x, start_y : 图像中左上角块的内部点的坐标
x_max_index, y_max_index : 计算出有多少行列
return 上述4值
'''


def find_postion(img_pixel, w, h):
    global T
    T = 20
    # 图像起点
    start_x = 0  # 起始纵坐标
    start_y = 0  # 起始横坐标
    findFirst = False
    # 寻找起点
    for i in range(205, h):
        if findFirst:
            break
        for j in range(100, w):
            px = img_pixel[j, i]
            # 红色 白色 蓝色
            if abs(px[0] - 245) + abs(px[1] - 83) + abs(px[2] - 103) < T or abs(px[0] - 235) + abs(px[1] - 233) + abs(
                            px[2] - 239) < T \
                    or abs(px[0] - 100) + abs(px[1] - 160) + abs(px[2] - 237) < T:
                start_x_l = i
                start_y_l = j - 20
                print(start_x_l, start_y_l)
                print(px)
                start_x = start_x_l + 63
                start_y = start_y_l + 63
                findFirst = True
                break;

    # print(start_x, start_y)
    y_max_index = 0
    x_max_index = 0
    tx = start_x
    ty = start_y
    px = img_pixel[start_y, start_x]
    while abs(px[0] - 245) + abs(px[1] - 83) + abs(px[2] - 103) < T or abs(px[0] - 235) + abs(px[1] - 233) + abs(
                    px[2] - 239) < T \
            or abs(px[0] - 100) + abs(px[1] - 160) + abs(px[2] - 237) < T:
        y_max_index += 1
        ty += 134
        px = img_pixel[ty, start_x]
    px = img_pixel[start_y, start_x]
    while abs(px[0] - 245) + abs(px[1] - 83) + abs(px[2] - 103) < T or abs(px[0] - 235) + abs(px[1] - 233) + abs(
                    px[2] - 239) < T \
            or abs(px[0] - 100) + abs(px[1] - 160) + abs(px[2] - 237) < T:
        x_max_index += 1
        tx += 134
        px = img_pixel[start_y, tx]
        # print(tx)
    print('xmax = ', x_max_index, 'ymax = ', y_max_index)
    return start_x, start_y, x_max_index, y_max_index


'''
组装java需要的数据
return 矩阵，起始点
'''


def get_java_map(img_pixel, start_x, start_y):
    tx = start_x
    ty = start_y
    # java 起始点
    j_sx = 0
    j_sy = 0
    # java 矩阵
    j_map = ''
    for i in range(0, 8):
        ty = start_y - 126 - 8
        if i != 0:
            tx = tx + 126 + 8
        for j in range(0, 6):
            ty = ty + 126 + 8
            px = img_pixel[ty, tx]
            if abs(px[0] - 235) + abs(px[1] - 233) + abs(
                            px[2] - 239) < T:
                j_map = j_map + '*0'
            else:
                if abs(px[0] - 245) + abs(px[1] - 83) + abs(px[2] - 103) < T:
                    j_map = j_map + '*-1'
                else:
                    if abs(px[0] - 100) + abs(px[1] - 160) + abs(px[2] - 237) < T:
                        j_map = j_map + '*1'
                        j_sx = i
                        j_sy = j
                        print(j_sx, j_sy)
    return j_map, j_sx, j_sy


'''
用于从jar包中获取结果点集（通关的路径）
x_max_index,y_max_index，java矩阵的长宽
return ：点集
'''


def get_point_list(x_max_index, y_max_index, j_sx, j_sy):
    path1 = os.path.abspath('.')
    startJVM("C:/Program Files/Java/jre1.8.0_20/bin/server/jvm.dll", "-ea",
             "-Djava.class.path=%s" % (path1 + '\oneline.jar'))
    JDClass = JClass("com.shxy.onelinegame.OneLine")
    jd = JDClass()
    # 获取java计算结果
    res = jd.forPython(str(x_max_index), str(y_max_index), j_map, str(j_sx), str(j_sy))
    # 结果点集
    return res.split('\n')


'''
start_x，start_y : 起始点像素位置，用于shell命令位置计算
point_list : 点集
'''


def run_adb_shell(start_x, start_y, point_list):
    first = True
    # 上一次点和当前点 index
    lx = 0;
    ly = 0;
    nx = 0;
    ny = 0;
    cmd = ''
    # loop 使用adb shell 命令模拟移动，index*实际像素 + 起始点像素
    for i in point_list:
        if first:
            p = i.split(',')
            lx = p[0]
            ly = p[1]
            first = False
            continue;
        p = i.split(',')
        nx = p[0]
        ny = p[1]
        cmd_x1 = start_x + int(lx) * (126 + 8)
        cmd_y1 = start_y + int(ly) * (126 + 8)
        cmd_x2 = start_x + int(nx) * (126 + 8)
        cmd_y2 = start_y + int(ny) * (126 + 8)

        # adb shell 先横坐标，后纵坐标
        cmd = 'adb shell input swipe {y1} {x1} {y2} {x2} {duration}'.format(
            x1=cmd_x1,
            y1=cmd_y1,
            x2=cmd_x2,
            y2=cmd_y2,
            duration=10
        )
        os.system(cmd)

        print(cmd)
        lx = nx
        ly = ny


if __name__ == '__main__':
    # 图像，宽高
    img, w, h = get_photo()
    # 像素图
    img_pixel = img.load()
    # 起始像素，矩阵大小
    start_x, start_y, x_max_index, y_max_index = find_postion(img_pixel, w, h)
    # 矩阵，矩阵内出发点(供Java使用)
    j_map, j_sx, j_sy = get_java_map(img_pixel, start_x, start_y)
    # 获取java结果
    point_list = get_point_list(x_max_index, y_max_index, j_sx, j_sy)
    # 根据结果执行abd shell
    run_adb_shell(start_x, start_y, point_list)
    time.sleep(2)
# finish！！！
