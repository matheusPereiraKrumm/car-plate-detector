from copy import deepcopy
from os import walk

import cv2 as cv


class Line:
    def __init__(self, inicio):
        self.inicio = inicio
        self.fim = 0
        self.tamanho = 0

    def set_fim(self, value):
        self.fim = value
        self.tamanho = value - self.inicio


def treeequals(line_act):
    last = line_act[0]
    count_intercection = 0
    cont_equals = 0
    for pixel in line_act:
        if pixel != last:
            cont_equals = cont_equals + 1
            if cont_equals >= 3:
                last = pixel
                count_intercection = count_intercection + 1
                cont_equals = 0
    return count_intercection >= 8


def diff_lower(line1, line2):
    if line1.inicio > line2.inicio:
        return line1.inicio - line2.fim
    else:
        return line2.inicio - line1.fim


def join_lines(line1, line2):
    if line1.inicio > line2.inicio:
        result = Line(line2.inicio)
        result.set_fim(line1.fim)
        return result
    else:
        result = Line(line1.inicio)
        result.set_fim(line2.fim)
        return result


def obtain_obj_line_final(imgParam):
    height = imgParam.shape[0]
    width = imgParam.shape[1]

    if width > 450:
        element3 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (17, 17))
    elif width > 280:
        element3 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    else:
        element3 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
    topHat_a = cv.morphologyEx(imgParam, 5, element3)
    result = imgParam - topHat_a
    fim = imgParam
    cv.threshold(result, 100, 255, cv.THRESH_BINARY, fim)
    i = 0
    list = []
    obj = None
    while i < height:
        line = imgParam[i]
        i = i + 1
        if treeequals(line):
            if obj is None:
                obj = Line(i)
                list.append(obj)
        else:
            if obj is not None:
                obj.set_fim(i)
                obj = None
    if obj is not None:
        obj.set_fim(height - 1)
    list.sort(key=lambda l: l.tamanho, reverse=True)
    obj_final = None
    i = 0
    while i < len(list):
        obj = list[i]
        i = i + 1
        if i > 1:
            if diff_lower(obj_final, obj) < 10:
                obj_final = join_lines(obj_final, obj)
            else:
                i = len(list)
        else:
            obj_final = Line(obj.inicio)
            obj_final.set_fim(obj.fim)
    return obj_final


def getAreaBoundingBox(contorno):
    largura, autura = getDimensions(contorno)
    return largura * autura


def getLargura(contorno):
    maxX = sorted(contorno, key=lambda x: x[0][0], reverse=True)[0][0][0]
    minX = sorted(contorno, key=lambda x: x[0][0], reverse=False)[0][0][0]
    return maxX - minX


def getAltura(contorno):
    maxY = sorted(contorno, key=lambda x: x[0][1], reverse=True)[0][0][1]
    minY = sorted(contorno, key=lambda x: x[0][1], reverse=False)[0][0][1]
    return maxY - minY


def getDimensions(contorno):
    return getLargura(contorno), getAltura(contorno)


def dimensoesParecidas(larguraPivo, larguraContorno, auturaPivo, auturaContorno):
    larguraParecida = (larguraContorno - 5) <= larguraPivo <= (larguraContorno + 5)
    auturaParecida = (auturaContorno - 5) <= auturaPivo <= (auturaContorno + 5)
    return auturaParecida


def procuraContornosParecidos(contours, quantidadeContornosParecidos):
    listaContornosEnquadrados = []
    for i in range(len(contours)):
        listaContornosParecidos = []
        pivo = contours[i]
        larguraPivo, auturaPivo = getDimensions(pivo)
        listaContornosParecidos.append(pivo)
        for j in range(i + 1, len(contours)):
            contorno = contours[j]
            larguraContorno, auturaContorno = getDimensions(contorno)
            if dimensoesParecidas(larguraPivo, larguraContorno, auturaPivo, auturaContorno):
                listaContornosParecidos.append(contorno)
        if len(listaContornosParecidos) > quantidadeContornosParecidos:
            listaContornosEnquadrados.append(listaContornosParecidos)

    ordenada = sorted(listaContornosEnquadrados, key=lambda c: getAltura(c[0]), reverse=True)
    return ordenada[0]


def removeInnersContorns(contornosParecidos):
    result = []
    for i in range(len(contornosParecidos)):
        pivo = contornosParecidos[i]
        maxXPivo = sorted(pivo, key=lambda x: x[0][0], reverse=True)[0][0][0]
        minXPivo = sorted(pivo, key=lambda x: x[0][0], reverse=False)[0][0][0]
        temIgual = False
        for j in range(len(result)):
            contorno = result[j]
            maxXContorno = sorted(contorno, key=lambda x: x[0][0], reverse=True)[0][0][0]
            minXContorno = sorted(contorno, key=lambda x: x[0][0], reverse=False)[0][0][0]
            if (maxXContorno >= maxXPivo and minXContorno <= minXPivo) \
                    or (maxXContorno <= maxXPivo and minXContorno >= minXPivo):
                temIgual = True
        if not temIgual:
            result.append(pivo)
    return result


def segment_caracter(imgParam):
    height = imgParam.shape[0]
    width = imgParam.shape[1]
    # imgParam = cv.medianBlur(imgParam, 5)

    if width > 280:
        element2 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    else:
        element2 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (1, 3))
    element3 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (17, 17))
    element4 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (15, 15))

    # cv.imshow("ori", imgParam)

    # topHat_a = cv.morphologyEx(imgParam, 5, element3)
    # cv.imshow("TH_ABERTA", topHat_a)

    topHat_c = cv.morphologyEx(imgParam, 6, element4)
    # cv.imshow("TH_FECHADO", topHat_c)

    key = 0
    paramThesh = 60
    while key != 32:
        fim = imgParam.copy()
        # cv.threshold(imgParam, paramThesh, 255, cv.THRESH_BINARY| cv.THRESH_OTSU, fim)
        # cv.imshow("thres", fim)

        # close = cv.morphologyEx(fim, cv.MORPH_GRADIENT, element2)
        # cv.imshow("close", close)

        gray = cv.bilateralFilter(fim, 11, 17, 17)
        edged = cv.Canny(gray, 30, 200)
        cv.imshow("canny", edged)
        # ret, thresh = cv.threshold(close, paramThesh, 255, 0)
        # dilate = cv.GaussianBlur(thresh, (1, 10001), 0)
        im2, contours, hierarchy = cv.findContours(edged, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        ordenado = sorted(contours, key=lambda x: getAreaBoundingBox(x), reverse=True)

        contornosParecidos = procuraContornosParecidos(ordenado, 7)
        contornosParecidos = removeInnersContorns(contornosParecidos)
        contornosParecidos = sorted(contornosParecidos, key=lambda x: x[0][0][0])

        for i in range(len(contornosParecidos)):
            contorno = contornosParecidos[i]
            maxX = sorted(contorno, key=lambda x: x[0][0], reverse=True)[0][0][0]
            minX = sorted(contorno, key=lambda x: x[0][0], reverse=False)[0][0][0]
            maxY = sorted(contorno, key=lambda x: x[0][1], reverse=True)[0][0][1]
            minY = sorted(contorno, key=lambda x: x[0][1], reverse=False)[0][0][1]

            imgcrop = fim[minY:maxY, minX:maxX]

            newImage = deepcopy(imgcrop)
            cv.imshow("Contorno " + str(i), newImage)

        key = cv.waitKey(0)
        if key == 83:
            paramThesh = paramThesh + 10
        if key == 81:
            paramThesh = paramThesh - 10
        print(key)
        print(paramThesh)
        cv.destroyAllWindows()
    #
    # open = cv.morphologyEx(fim, cv.MORPH_OPEN, element2)
    # cv.imshow("open", open)
    #
    # close = cv.morphologyEx(fim, cv.MORPH_CLOSE, element2)
    # cv.imshow("close", close)

    #
    # result = ((imgParam + topHat_a) - topHat_c) - open
    #
    # cv.imshow("thre", result)

    # cv.imshow("fewH", fim)
    # key = cv.waitKey(0)
    # while key != 32:
    #     print key
    #     key = cv.waitKey(0)
    # cv.destroyAllWindows()


if __name__ == '__main__':
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    directory = 'amostra'

    for (a, b, files) in walk(directory):
        for filename in files:
            img = cv.imread((directory + '/' + filename), 0)
            imgOri = cv.imread((directory + '/' + filename), 0)

            objFinal = obtain_obj_line_final(img)
            imgcrop = imgOri[objFinal.inicio - 10:objFinal.fim][0:]

            newImage = deepcopy(imgcrop)
            segment_caracter(newImage)

            imgcrop = cv.medianBlur(imgcrop, 5)

            # cv.imshow("fewH", imgcrop)
            # key = cv.waitKey(0)
            # while key != 32:
            #     if key == 107:
            #         print filename
            #     key = cv.waitKey(0)
            # cv.destroyAllWindows()

            # noNoise = cv.morphologyEx(img, cv.MORPH_TOPHAT, kernel)
            # img = img - noNoise
            # img = cv.morphologyEx(img, cv.MORPH_OPEN, kernel)
            # img = cv.morphologyEx(img, cv.MORPH_GRADIENT, kernel)
            # cv.imshow(filename, img)
