"""
MIT License

Copyright (c) 2024 - "Rising Edge" Group

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from bs4 import BeautifulSoup
from typing import List, Tuple
from urllib.parse import urlparse
from .notification_alerts import FlagAlerts
import requests
import re
from . import utils


class echoSession(requests.Session):
    main_url = None  # TODO: Refactorize
    _available_targets = None  # TODO: Refactorize

    def __init__(self, instance_url, identity_cookie, *args, **kwargs):
        """Initializes an `echoSession` with the specified base URL and identity cookie.

        Args:
            instance_url (str): The base URL of the echoCTF platform instance.
            identity_cookie (str): Cookie string for identity verification.
            *args: Variable length argument list passed to `requests.Session`.
            **kwargs: Arbitrary keyword arguments passed to `requests.Session`.
        """
        parsed_url = urlparse(instance_url)
        self.main_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        super().__init__(*args, **kwargs)
        self.cookies["_identity-red"] = identity_cookie

    def spin_target(self, target_id: int) -> None:
        """Sends a request to "spin" a target machine by its ID.

        Args:
            target_id (int): Unique identifier for the target machine.
        """
        target_site_html = self.get(f"{self.main_url}/target/{target_id}").text
        csrf_token = utils.extract_csrf_token(target_site_html)

        self.post(
            url=f"{self.main_url}/target/{target_id}/spin",
            data={"_csrf-red": csrf_token},
        )

    # TODO: Refactorize and test even more
    def targets_list(self) -> List[Tuple[str, int]]:
        """Fetches and returns a list of available targets in the form of (target_name, target_id).

        Returns:
            List[Tuple[str, int]]: A list of tuples, each containing a target's name and its unique ID.
        """
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
        """Determines if a specific target is currently active.

        Args:
            target_id (int): The ID of the target to check.

        Returns:
            bool: True if the target is active, False otherwise.
        """
        raise NotImplementedError

    def claim_flag(self, flag: str) -> FlagAlerts:
        """Attempts to claim a flag and returns the result status.

        Args:
            flag (str): The flag string to be claimed.

        Returns:
            FlagAlerts: Enum indicating the status of the flag claim attempt.
        """
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
