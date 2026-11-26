# AllStarLink HTTP registration compatibility

Reviewed `res/res_rpt_http_registrations.c` from AllStarLink/app_rpt on 2026-11-10,
source blob `c995988cb81b823a6d725aadd3ea160b15097a21`:
https://github.com/AllStarLink/app_rpt/blob/master/res/res_rpt_http_registrations.c

The endpoint retains the client's JSON shape and success detection. Tests cover
omitted/explicit ports, authentication rejection, validation, proxy trust, and failures.
The default port when omitted is IAX's 4569. The client requires external HTTPS;
terminate TLS at a configured ingress, forwarding only through trusted proxy peers.
Do not expose the internal HTTP listener directly on an untrusted network.

Malformed input, request limits, and infrastructure failures return non-2xx statuses.
The client can leave its displayed registration flag unchanged after such failures;
this is an upstream limitation, not evidence of a current directory entry. Directory
expiry remains authoritative. Authentication rejection uses a compatible 200 response
with generic failure text. The service publishes before returning success. Tests are
contract fixtures and do not launch Asterisk itself.
