// C++ / WebAssembly kernel para relación de impedancia sísmica SH 1D y rigidez secante hiperbólica p-y
extern "C" {
  double impedanceRatio(double rho1, double vs1, double rho2, double vs2) {
    return (rho1 * vs1) / (rho2 * vs2);
  }

  double pySecantStiffness(double p_ult, double k_ini, double z, double y) {
    return (p_ult * k_ini * z) / (p_ult + k_ini * z * y);
  }
}
