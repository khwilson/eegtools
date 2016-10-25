import os
import zipfile
from io import BytesIO

import numpy as np
from scipy import io
from six.moves import urllib

from .shared import Recording, data_source


__all__ = ['load', 'subjects', 'sessions']

sessions = 'aa al av aw ay'.split()
subjects = sessions  # Legacy name, since sessions is more accurate.

BASE_URL = 'http://bbci.de'
URL_TRAIN = '{base_url}/competition/download/competition_iii/berlin/100Hz/data_set_IVa_{{subject}}_mat.zip'.format(base_url=BASE_URL)
URL_TEST = '{base_url}/competition/iii/results/berlin_IVa/true_labels_{{subject}}.mat'.format(base_url=BASE_URL)


LICENSE = '''Each participant has to agree to give reference to the group(s)
which recorded the data and to cite (one of) the paper listed in the respective
description in each of her/his publications where one of those data sets is
analyzed. Furthermore, we request each author to report any publication
involving BCI Competiton data sets to us for including it in our list.

[1] Guido Dornhege, Benjamin Blankertz, Gabriel Curio, and Klaus-Robert
    Müller. Boosting bit rates in non-invasive EEG single-trial
    classifications by feature combination and multi-class paradigms. IEEE
    Trans. Biomed. Eng., 51(6):993-1002, June 2004.

Note that the above reference describes an older experimental setup. A new
paper analyzing the data sets as provided in this competition and presenting
the feedback results will appear soon.
'''


def load_mat(mat_train, mat_test, rec_id):
  """
  Load BCI Comp. 3.4a specific Matlab files.

  :param str mat_train: The location of the training data
  :param str mat_test: The location of the testing data
  :param str rec_id: The recording id. Looks like 'bcicomp3.4a-{subject}'
  :returns: The loaded recording
  :rtype: Recording
  """
  mat = io.loadmat(mat_train, struct_as_record=True)
  mat_true = io.loadmat(mat_test, struct_as_record=True)

  # get simple info from MATLAB files
  X = mat['cnt'].astype(np.float32).T * 0.1
  nfo, mrk = mat['nfo'][0][0], mat['mrk'][0][0]

  sample_rate = float((nfo['fs'])[0][0])
  dt = np.ones(X.shape[1]-1) / sample_rate
  chan_lab = [str(c[0]) for c in nfo['clab'].flatten()]

  # extract labels from both MATLAB files
  offy = mrk['pos'].flatten()
  tr_y = mrk['y'].flatten()
  all_y = mat_true['true_y'].flatten()
  assert np.all((tr_y == all_y)[np.isfinite(tr_y)]), 'labels do not match.'

  class_lab = [str(c[0]) for c in (mrk['className'])[0]]
  events = np.vstack([all_y, offy, offy + 3.5 * sample_rate]).astype(int)
  event_lab = dict(zip(np.unique(events[0]), class_lab))

  folds = np.where(np.isfinite(tr_y), -1, 1).tolist()

  return Recording(X=X, dt=dt, chan_lab=chan_lab,
    events=events, event_lab=event_lab, folds=folds,
    rec_id=rec_id, license=LICENSE)


def load(subject, ds=data_source(), user='bci@mailinator.com',
         password='laichucaij'):
  """
  Public API for loading hte BCI competition data sets.

  :param str subject: Which subject to laod
  :param np.DataSource ds: The numpy data source from which to load the data.
    Will download if not already downloaded. Defaults set in the shared.py file.
  :param str user: The user name under which to load the data
  :param str password: The password for loading the data
  :returns: The loaded data for the relevant subject
  :rtype: Recording
  """
  # get HTTP authentication going
  password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
  password_mgr.add_password(None, BASE_URL, user, password)
  handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
  opener = urllib.request.build_opener(urllib2.HTTPHandler, handler)
  urllib.request.install_opener(opener)

  # Load the training set. We need to get a *seekable* file from a zip file.
  # So we wrap this in a BytesIO
  tr = zipfile.ZipFile(ds.open(URL_TRAIN.format(subject=subject)))
  tr_mat = BytesIO(tr.read('100Hz/data_set_IVa_{subject}.mat'.format(subject=subject)))

  # Load test labels that were made available after the competition.
  te_mat = ds.open(URL_TEST.format(subjecdt=subject))

  return load_mat(tr_mat, te_mat, 'bcicomp3.4a-{subject}'.format(subject=subject))
