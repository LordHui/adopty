"""Ista algorithm for the LASSO
"""

import numpy as np
from time import time

from .utils import cost, grad, soft_thresholding
from .ista import ista


def fista(D, x, lmbd, z_init=None, max_iter=100, tol=1e-8):
    """FISTA for resolution of the sparse coding

    Parameters
    ----------
    D : array, shape (n_atoms, n_dimensions)
        Dictionary used for the sparse coding
    x : array, shape (n_trials, n_dimensions)
        Signal to encode on D
    lmbd : float
        Regularization parameter of the sparse coding
    z_init : array, shape (n_trial, n_atoms) or None
        Initial value of the activation codes
    max_iter : int
        Maximal number of iteration for ISTA

    Returns
    -------
    z_hat : array, shape (n_trial, n_atoms)
        Estimated sparse codes
    cost_ista : list
        Cost accross the iterations
    times : list
        Time taken by each iteration
    """
    n_trials = x.shape[0]
    n_atoms = D.shape[0]

    L = np.linalg.norm(D.dot(D.T), 2)
    step_size = 1 / L

    # Generate an initial point
    if z_init is not None:
        z_hat = np.copy(z_init)
    else:
        z_hat = np.zeros((n_trials, n_atoms))

    y_hat = z_hat
    tk = 1

    times = []
    cost_ista = [cost(z_hat, D, x, lmbd)]
    for it in range(max_iter):
        t_start_iter = time()

        z_hat_aux = z_hat
        y_hat -= step_size * grad(y_hat, D, x)
        z_hat = soft_thresholding(y_hat, lmbd * step_size)
        diff = z_hat - z_hat_aux

        tk_new = (1 + np.sqrt(1 + 4 * tk * tk)) / 2
        y_hat = z_hat + (tk - 1) / tk_new * diff
        tk = tk_new

        times += [time() - t_start_iter]
        cost_ista += [cost(z_hat, D, x, lmbd)]
        dz = diff.ravel().dot(diff.ravel())
        if dz < tol:
            break

    return z_hat, cost_ista, times