# The NONMEM Model class
import re

import pharmpy.model
import pharmpy.plugins.nonmem.input
from pharmpy.parameter import ParameterSet
from pharmpy.plugins.nonmem.results import NONMEMChainedModelfitResults

from .nmtran_parser import NMTranParser


class Model(pharmpy.model.Model):
    def __init__(self, src, **kwargs):
        parser = NMTranParser()
        self.source = src
        if not self.source.filename_extension:
            self.source.filename_extension = '.ctl'
        self.name = self.source.path.stem
        self.control_stream = parser.parse(src.code)
        if self.source.path.is_file():
            lst_path = self.source.path.with_suffix('.lst')
            if lst_path.exists():
                num_est = len(self.control_stream.get_records('ESTIMATION'))
                self.modelfit_results = NONMEMChainedModelfitResults(lst_path, num_est)
        self.input = pharmpy.plugins.nonmem.input.ModelInput(self)

    @staticmethod
    def detect(src, *args, **kwargs):
        """ Check if src represents a NONMEM control stream
        i.e. check if it is a file that contain $PRO
        """
        return bool(re.search(r'^\$PRO', src.code, re.MULTILINE))

    def update_source(self, force=False):
        """Update the source"""
        if self.input._dataset_updated:
            # FIXME: If no name set use the model name. Set that when setting dataset to input!
            datapath = self.input.dataset.pharmpy.write_csv(force=force)
            self.input.path = datapath

            data_record = self.control_stream.get_records('DATA')[0]

            label = self.input.dataset.columns[0]
            data_record.ignore_character_from_header(label)

            # Remove IGNORE/ACCEPT. Could do diff between old dataset and find simple
            # IGNOREs to add i.e. for filter out certain ID.
            del(data_record.ignore)
            del(data_record.accept)
        super().update_source()

    def validate(self):
        """Validates NONMEM model (records) syntactically."""
        self.control_stream.validate()

    @property
    def parameters(self):
        """Get the ParameterSet of all parameters
        """
        next_theta = 1
        params = ParameterSet()
        for theta_record in self.control_stream.get_records('THETA'):
            thetas = theta_record.parameters(next_theta)
            params.update(thetas)
            next_theta += len(thetas)
        next_omega = 1
        for omega_record in self.control_stream.get_records('OMEGA'):
            omegas, next_omega = omega_record.parameters(next_omega)
            params.update(omegas)
        next_sigma = 1
        for sigma_record in self.control_stream.get_records('SIGMA'):
            sigmas, next_sigma = sigma_record.parameters(next_sigma)
            params.update(sigmas)
        return params

    def __str__(self):
        return str(self.control_stream)
