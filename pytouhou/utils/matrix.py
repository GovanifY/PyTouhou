#TODO: find/learn to use a proper lib

from math import sin, cos

class Matrix(object):
    def __init__(self):
        self.data = [[0] * 4 for i in xrange(4)]


    def mult(self, other_matrix):
        result = Matrix()
        for i in xrange(4):
            for j in xrange(4):
                result.data[i][j] = sum(self.data[i][a] * other_matrix.data[a][j] for a in xrange(4))
        return result


    @classmethod
    def get_translation_matrix(cls, x, y, z):
        matrix = cls()
        matrix.data[0][0] = 1
        matrix.data[1][1] = 1
        matrix.data[2][2] = 1
        matrix.data[3][3] = 1
        matrix.data[0][3] = x
        matrix.data[1][3] = y
        matrix.data[2][3] = z
        return matrix


    @classmethod
    def get_scaling_matrix(cls, x, y, z):
        matrix = cls()
        matrix.data[0][0] = x
        matrix.data[1][1] = y
        matrix.data[2][2] = z
        matrix.data[3][3] = 1
        return matrix


    @classmethod
    def get_rotation_matrix(cls, angle, axis):
        """Only handles axis = x, y or z."""
        matrix = cls()
        matrix.data[3][3] = 1
        if axis == 'x':
            matrix.data[0][0] = 1
            matrix.data[1][1] = cos(angle)
            matrix.data[1][2] = -sin(angle)
            matrix.data[2][1] = sin(angle)
            matrix.data[2][2] = cos(angle)
        elif axis == 'y':
            matrix.data[0][0] = cos(angle)
            matrix.data[0][2] = sin(angle)
            matrix.data[2][0] = -sin(angle)
            matrix.data[2][2] = cos(angle)
            matrix.data[1][1] = 1
        elif axis == 'z':
            matrix.data[0][0] = cos(angle)
            matrix.data[0][1] = -sin(angle)
            matrix.data[1][0] = sin(angle)
            matrix.data[1][1] = cos(angle)
            matrix.data[2][2] = 1
        else:
            raise Exception
        return matrix
