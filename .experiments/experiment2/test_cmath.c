#include <complex.h>
#include <stdio.h>
// #include <tgmath.h>

int main() {
    double complex z = I * I;     // imaginary unit squared
    printf("I * I = %.1f%+.1fi\n", creal(z), cimag(z));
    return 0;
}
