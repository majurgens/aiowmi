import struct
from .orpcthat import ORPCTHAT
from .objref_custom import ObjRefCustom
from .activation_blob import ActivationBlob
from .scm_reply_info_data import ScmReplyInfoData
from .props_out_info import PropsOutInfo
from ..tools import is_fqdn
from .interface import NdrInterface


"""
ORPCTHAT
flags
\x01\x00\x00\x00
ext
\x00\x00\x00\x00


\x00\x00\x02\x00`\x03\x00\x00`\x03\x00\x00MEOW\x04\x00\x00\x00\xa3\x01....
"""


class RemoteCreateInstanceResponse(NdrInterface):

    FMT1_32 = '<LLL'
    FMT1_64 = '<QLL'

    FMT1_32_SZ = struct.calcsize(FMT1_32)

    def __init__(self, target: str, data: bytes):
        self.orpcthat, offset = ORPCTHAT.from_data(data, offset=0)

        # activation_blobs
        (
            self.referent_id,
            _,
            size
        ) = struct.unpack_from(self.FMT1_32, data, offset)
        offset += self.FMT1_32_SZ

        self.objref = ObjRefCustom.from_data(data, offset, size)
        offset += size

        ab_data = ActivationBlob.from_data(self.objref.object_data)

        self.error_code, = struct.unpack_from('<L', data, offset)
        self.props_out_info = PropsOutInfo(ab_data.properties[0])
        self.scm_reply_info_data = ScmReplyInfoData(ab_data.properties[1])
        self._binding = None
        target = target.upper()
        self._target = target.partition('.')[0] if is_fqdn(target) else target

        assert self.error_code == 0, f'error code: {self.error_code}'

    def get_binding(self):
        if self._binding is None:
            for bindingtuple in self.scm_reply_info_data.str_bindings:
                tower_id, binding = bindingtuple
                if tower_id != 7:
                    continue

                if binding.find('[') >= 0:
                    binding, _, port = binding.strip(']\x00').partition('[')
                    port = int(port)
                else:
                    port = 0

                if binding.upper().find(self._target) < 0:
                    continue

                self._binding = (binding, port)
        return self._binding

    def get_ipid(self) -> int:
        return self.props_out_info.objref.ipid