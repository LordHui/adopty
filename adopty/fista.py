"""Ista algorithm for the LASSO
"""

import numpy as np
from time import time

from .loss_and_gradient import cost_lasso, grad, soft_thresholding


def fista(D, x, lmbd, z_init=None, max_iter=100, stopping_criterion=None):
    """FISTA for resolution of the sparse coding

    Parameters
    ----------
    D : array, shape (n_atoms, n_dim)
        Dictionary used for the sparse coding
    x : array, shape (n_samples, n_dim)
        Signal to encode on D
    lmbd : float
        Regularization parameter of the sparse coding
    z_init : array, shape (n_trial, n_atoms) or None
        Initial value of the activation codes
    max_iter : int
        Maximal number of iteration for ISTA
    stopping_critrion: callable or None
        If it is a callable, it is call with the list of the past costs
        and the algorithm is stopped if it returns True.

    Returns
    -------
    z_hat : array, shape (n_trial, n_atoms)
        Estimated sparse codes
    cost_ista : list
        Cost accross the iterations
    times : list
        Time taken by each iteration
    """
    n_samples = x.shape[0]
    n_atoms = D.shape[0]

    L = np.linalg.norm(D.dot(D.T), 2)
    step_size = 1 / L

    # Generate an initial point
    if z_init is not None:
        z_hat = np.copy(z_init)
    else:
        z_hat = np.zeros((n_samples, n_atoms))

    y_hat = z_hat
    tk = 1

    times = []
    cost_ista = [cost_lasso(z_hat, D, x, lmbd)]
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
        cost_ista += [cost_lasso(z_hat, D, x, lmbd)]

        # Stopping criterion for the convergence
        if callable(stopping_criterion) and stopping_criterion(cost_ista):
            break

    return z_hat, cost_ista, times
