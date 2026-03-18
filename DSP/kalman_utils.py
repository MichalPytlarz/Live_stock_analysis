import numpy as np
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise


def apply_kalman_filter_filterpy(prices):
    """
    Applies a Kalman filter to price data.
    Returns filtered prices and velocities.
    """
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.x = np.array([[prices[0]], [0.]])
    kf.F = np.array([[1., 1.], [0., 1.]])
    kf.H = np.array([[1., 0.]])
    kf.P *= 1000.
    kf.R = 5
    kf.Q = Q_discrete_white_noise(dim=2, dt=1., var=0.01)
    kalman_means = []
    velocities = []
    for z in prices:
        kf.predict()
        kf.update(z)
        kalman_means.append(kf.x[0, 0])
        velocities.append(kf.x[1, 0])

    
    return kalman_means, velocities


def get_kalman_dashboard_data(df):
    """
    Given a DataFrame with 'close' prices, returns DataFrame with Kalman filter results.
    """
    if df.empty or 'close' not in df.columns:
        return None
    prices = df['close'].values
    kalman_means, velocities = apply_kalman_filter_filterpy(prices)
    df = df.copy()
    df['Kalman_Price'] = kalman_means
    df['Kalman_Velocity'] = velocities
    return df
