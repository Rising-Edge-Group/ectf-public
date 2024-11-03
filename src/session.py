from bs4 import BeautifulSoup
from typing import List, Tuple
from urllib.parse import urlparse
from notification_alerts import FlagAlerts
import requests
import re
import utils


class echoSession(requests.Session):
    main_url = None  # TODO: Refactorize
    _available_targets = None  # TODO: Refactorize

    def __init__(self, instance_url, identity_cookie, *args, **kwargs):
        parsed_url = urlparse(instance_url)
        self.main_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        super().__init__(*args, **kwargs)
        self.cookies["_identity-red"] = identity_cookie

    def spin_target(self, target_id: int) -> None:
        """Sends a spin request to echoCTF for `target_id` machine"""
        target_site_html = self.get(f"{self.main_url}/target/{target_id}").text
        csrf_token = utils.extract_csrf_token(target_site_html)

        self.post(
            url=f"{self.main_url}/target/{target_id}/spin",
            data={"_csrf-red": csrf_token},
        )

    # NOTE: "https://echoctf.red/targets?target-page=1"
    def targets_list(self) -> List[Tuple[str, int]]:
        """Returns a list of tuples in the next format: (target_name, target_number)"""
        targets_html_site = self.get(f"{self.main_url}/targets").text
        html_parser = BeautifulSoup(targets_html_site, "html.parser")

        # Find "Step Forward Button" tag and extract last page from that
        last_page_tag = html_parser.find_all(class_="page-item last")[0].contents[0]
        pages_amount = int(last_page_tag.attrs["data-page"]) + 1

        return_list = []
        # We are parsing the first page two times. This can be optimized!
        for page in range(1, pages_amount + 1):
            actual_page_html = self.get(
                f"{self.main_url}/targets", params={"target-page": page}
            ).text
            html_parser = BeautifulSoup(actual_page_html, "html.parser")

            def has_data_key_atrr(tag):
                return tag.has_attr("data-key")

            for target_tag in html_parser.find_all(has_data_key_atrr):
                # We need to separate the target title from the ip
                pattern_match = re.match(r"^([^\d]+)", target_tag.text)
                if pattern_match is not None:
                    return_list.append(
                        (pattern_match.group(1), target_tag.attrs["data-key"])
                    )

        self._available_targets = return_list
        return return_list

    def is_active(self, target_id: int) -> bool:
        raise NotImplementedError

    def claim_flag(self, flag: str) -> FlagAlerts:
        main_page_html = self.get(f"{self.main_url}/dashboard").text
        csrf_token = utils.extract_csrf_token(main_page_html)
        self.post(
            url=f"{self.main_url}/claim",
            data={"_csrf-red": csrf_token, "hash": flag},
            headers={
                "X-Csrf-Token": csrf_token,
                "X-Pjax": "true",
                "X-Pjax-Container": "#claim-flag",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        possible_patterns = {
            FlagAlerts.FLAG_DOES_NOT_EXIST: re.compile(
                rf"Flag \[<strong>{flag}</strong>\] does not exist!"
            ),
            FlagAlerts.FLAG_CLAIMED_BEFORE: re.compile(r"Flag \[.*\] claimed before"),
            FlagAlerts.FLAG_CLAIMED_FOR_POINTS: re.compile(
                r"Flag \[.*\] claimed for \d{1,3}(?:,\d{3})* points"
            ),
            FlagAlerts.SERVICE_DISCOVERY_REQUIRED: re.compile(
                "You need to discover at least one service before claiming a flag for this system."
            ),
            FlagAlerts.ACCESS_DENIED: re.compile(
                "You cannot claim this flag. You don't have access to this network."
            ),
        }

        after_submission_html = self.get(f"{self.main_url}/dashboard").text
        html_parser = BeautifulSoup(after_submission_html, "html.parser")
        for script_tag in html_parser.find_all("script"):
            if not script_tag.string:
                continue
            for script_line in script_tag.string.splitlines():
                if not script_line.strip().startswith("$.notify"):
                    continue
                for alert_type, pattern in possible_patterns.items():
                    if pattern.search(script_line):
                        return alert_type

        return FlagAlerts.UNKNOWN
