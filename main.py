from copy import deepcopy
from os import walk

import cv2 as cv


class Line:
    def __init__(self, begin):
        self.begin = begin
        self.end = 0
        self.size = 0

    def set_end(self, value):
        self.end = value
        self.size = value - self.begin


def tree_equals(line_act):
    """
        Conta quantas intercecções há na linha de pixel, que após a intercecção tenham continuação de 3 pixels do novo valor
    :param line_act:
    :return: Verdadeiro caso encontre no minimo 8 intercecções
    """
    last = line_act[0]
    count_intersection = 0
    cont_equals = 0
    for pixel in line_act:
        if pixel != last:
            cont_equals = cont_equals + 1
            if cont_equals >= 3:
                last = pixel
                count_intersection = count_intersection + 1
                cont_equals = 0

    return count_intersection >= 8


def diff_lower(line1, line2):
    """
    :param line1:
    :param line2:
    :return: A quantidade de linhas entre os dois objetos de linha
    """
    if line1.begin > line2.begin:
        return line1.begin - line2.end
    else:
        return line2.begin - line1.end


def join_lines(line1, line2):
    """
        Defini que o inicio do novo Objeto linha é o menor inicio e maior fim entre os objetos
        linha passados como parametro
    :param line1:
    :param line2:
    :return: Novo objeto linha juntanto os dois passados como parametro
    """
    if line1.begin > line2.begin:
        result = Line(line2.begin)
        result.set_end(line1.end)
        return result
    else:
        result = Line(line1.begin)
        result.set_end(line2.end)
        return result


def obtain_obj_line_final(img):
    """
        Aplica-se um Top Hat de Abertura e subtrai da imagem original
        Binariza-se a imagem
        Procura por possiveis linha que podem ser a placa
        Encontra a maior sequencia de possiveis linha para ser a placa
    :param img:
    :return: Valor encontrado de maior sequencia do conjunto de possiveis placas
    """
    height = img.shape[0]
    width = img.shape[1]

    if width > 450:
        element3 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (17, 17))
    elif width > 280:
        element3 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    else:
        element3 = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))

    top_hat_a = cv.morphologyEx(img, cv.MORPH_TOPHAT, element3)
    result = img - top_hat_a
    end = img

    cv.threshold(result, 100, 255, cv.THRESH_BINARY, end)

    i = 0
    list = []
    obj = None
    while i < height:
        line = img[i]
        i = i + 1
        if tree_equals(line):
            if obj is None:
                obj = Line(i)
                list.append(obj)
        else:
            if obj is not None:
                obj.set_end(i)
                obj = None

    if obj is not None:
        obj.set_end(height - 1)

    list.sort(key=lambda l: l.size, reverse=True)

    result = None
    i = 0
    while i < len(list):
        obj = list[i]
        i = i + 1
        if i > 1:
            if diff_lower(result, obj) < 10:
                result = join_lines(result, obj)
            else:
                i = len(list)
        else:
            result = Line(obj.begin)
            result.set_end(obj.end)

    return result


def bounding_box_area(contour):
    """
        Busca as dimensões do contorno
    :param contour:
    :return: Area multiplicado pela altura do contorno
    """
    width, height = dimensions(contour)
    return width * height


def width(contour):
    """
    :param contour:
    :return: A diferença entre o maior e menor valor no eixo X do contorno
    """
    max_x = sorted(contour, key=lambda x: x[0][0], reverse=True)[0][0][0]
    min_x = sorted(contour, key=lambda x: x[0][0], reverse=False)[0][0][0]
    return max_x - min_x


def height(contour):
    """
    :param contour:
    :return: A diferença entre o maior e menor valor no eixo Y do contorno
    """
    max_y = sorted(contour, key=lambda x: x[0][1], reverse=True)[0][0][1]
    min_y = sorted(contour, key=lambda x: x[0][1], reverse=False)[0][0][1]
    return max_y - min_y


def dimensions(contour):
    """
    :param contour:
    :return: Largura e Altura do contorno
    """
    return width(contour), height(contour)


def similar_dimensions(height_pivo, height_contour):
    """
    :param height_pivo:
    :param height_contour:
    :return: Verdadeiro caso a primeira altura seja igual a segunda podendo variar em 5 pixels para cima ou para baixo
    """
    return (height_contour - 5) <= height_pivo <= (height_contour + 5)


def similar_contours(contours, similar_contours_count):
    """
        Procura entre os contornos e agrupa por altura parecidas
    :param contours:
    :param similar_contours_count:
    :return: O Conjunto de contornos com maior altura
    """
    framed_contours = []

    for i in range(len(contours)):
        similar_contours = []
        pivo = contours[i]
        width_pivo, height_pivo = dimensions(pivo)
        similar_contours.append(pivo)

        for j in range(i + 1, len(contours)):
            contour = contours[j]
            width_contour, height_contour = dimensions(contour)

            if similar_dimensions(height_pivo, height_contour):
                similar_contours.append(contour)

        if len(similar_contours) > similar_contours_count:
            framed_contours.append(similar_contours)

    return sorted(framed_contours, key=lambda c: height(c[0]), reverse=True)[0]


def remove_inners_contours(similar_contours):
    """
        Remove contornos que possam estar dentro de outro contorno do conjunto.
    :param similar_contours:
    :return: O novo conjunto sem contorno dentro dos contornos do mesmo cnjunto.
    """
    result = []
    for i in range(len(similar_contours)):
        pivo = similar_contours[i]

        max_x_pivo = sorted(pivo, key=lambda x: x[0][0], reverse=True)[0][0][0]
        min_x_pivo = sorted(pivo, key=lambda x: x[0][0], reverse=False)[0][0][0]

        has_equal = False
        for j in range(len(result)):
            contour = result[j]

            max_x_contour = sorted(contour, key=lambda x: x[0][0], reverse=True)[0][0][0]
            min_x_contour = sorted(contour, key=lambda x: x[0][0], reverse=False)[0][0][0]

            if (max_x_contour >= max_x_pivo and min_x_contour <= min_x_pivo) \
                    or (max_x_contour <= max_x_pivo and min_x_contour >= min_x_pivo):
                has_equal = True

        if not has_equal:
            result.append(pivo)

    return result


def segment_character(img):
    """
        Aplica-se o algoritmo Canny na imagem
        Imprime a imagem refencia para a segmentação
        Encontra os contornos da imagem
        Busca o conjunto de contornos com maior altura por similaridade na altura da dimensão do contorno
        Remove os contornos que possam estar dentro de outros contornos do conjunto
        Ordena os contornos do conjunto da esquerda para a direita
        Imprime os caracteres encontrados na ordem que deveriam estar na placa
    :param img:
    """
    end = img.copy()

    gray = cv.bilateralFilter(end, 11, 17, 17)
    edged = cv.Canny(gray, 30, 200)
    cv.imshow("Processed Image", edged)

    im2, contours, hierarchy = cv.findContours(edged, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    contours_sorted = sorted(contours, key=lambda x: bounding_box_area(x), reverse=True)

    similar_contours_found = similar_contours(contours_sorted, 7)
    similar_contours_found = remove_inners_contours(similar_contours_found)
    similar_contours_found = sorted(similar_contours_found, key=lambda x: x[0][0][0])

    for i in range(len(similar_contours_found)):
        contour = similar_contours_found[i]
        max_x = sorted(contour, key=lambda x: x[0][0], reverse=True)[0][0][0]
        min_x = sorted(contour, key=lambda x: x[0][0], reverse=False)[0][0][0]
        max_y = sorted(contour, key=lambda x: x[0][1], reverse=True)[0][0][1]
        min_y = sorted(contour, key=lambda x: x[0][1], reverse=False)[0][0][1]

        img_crop = end[min_y:max_y, min_x:max_x]
        img_new = deepcopy(img_crop)
        cv.imshow("Contour " + str(i), img_new)

    key = cv.waitKey(0)
    while key != 32:
        key = cv.waitKey(0)

    cv.destroyAllWindows()


if __name__ == '__main__':
    """ 
        Encontra a posição de linhas da imgem que contem a placa e tenta segmentar os caracteres
    """
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    directory = 'samples'

    for (a, b, files) in walk(directory):
        for filename in files:
            img = cv.imread((directory + '/' + filename), 0)
            imgOri = cv.imread((directory + '/' + filename), 0)
            print(directory + '/' + filename)
            objFinal = obtain_obj_line_final(img)
            img_crop = imgOri[objFinal.begin - 10:objFinal.end][0:]

            img_new = deepcopy(img_crop)
            segment_character(img_new)
