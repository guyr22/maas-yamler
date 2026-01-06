from typing import Dict, Any
from formatters.job_formatter import JobFormatter
from config import CERTS_CONFIG


class HttpSDJobFormatter(JobFormatter):
    @classmethod
    def format_job(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        cls.format_common_fields(data)
        
        config_details = []

        for url_endpoint in data.pop("url_endpoints", []):
            config_details.append({"url": url_endpoint})

        if "basic_auth" in data:
            basic_auth = data.pop("basic_auth")
            for url in config_details:
                url['basic_auth'] = basic_auth
            
        if "refresh_interval" in data:
            refresh_interval = cls.convert_number_to_seconds(data.pop("refresh_interval"))
            for url in config_details:
                url['refresh_interval'] = refresh_interval

        data["http_sd_configs"] = config_details

        if data.pop('certs', False):
            if not data.get('tls_config'):
                data['tls_config'] = {}
            
            data['tls_config']['ca_file'] = CERTS_CONFIG['ca_file']
            data['tls_config']['cert_file'] = CERTS_CONFIG['cert_file']
            data['tls_config']['key_file'] = CERTS_CONFIG['key_file']


        return data