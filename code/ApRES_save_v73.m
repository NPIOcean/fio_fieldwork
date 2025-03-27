load vsr_raw
use out_vsr

load dh_raw
dh_time = t_dh_raw;

dh_f36 = vfilt(vfilt(dh_raw',3,'median'),36/2)';

save fio_ApRES_01 vsr_time vsr_raw vsr_mean vsr_LP vsr_raw_error vsr_mean_error dh_time dh_raw dh_f36 -v7.3