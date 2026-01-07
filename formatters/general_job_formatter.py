from typing import Dict, Any
from formatters.job_formatter import JobFormatter
from config import CERTS_CONFIG


class GeneralJobFormatter(JobFormatter):
    @classmethod
    def format_job(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        data = cls.format_common_fields(data)
        data['static_configs'] = data.get("static_configs", [{}])
        data['static_configs'][0]['targets'] = data.pop("targets", [])

        if data.pop('certs', False):
            if not data.get('tls_config'):
                data['tls_config'] = {}
            
            data['tls_config']['ca_file'] = CERTS_CONFIG['ca_file']
            data['tls_config']['cert_file'] = CERTS_CONFIG['cert_file']
            data['tls_config']['key_file'] = CERTS_CONFIG['key_file']

        return data
