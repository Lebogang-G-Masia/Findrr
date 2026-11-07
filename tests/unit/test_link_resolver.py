"""Unit tests for destination link classification and ATS prioritization (Module 4, FR-014)."""

from findrr.search.link_resolver import (
    LinkResolver,
    classify_url_destination,
    extract_candidate_links_from_html,
)


def test_classify_url_destination_ats():
    assert classify_url_destination("https://boards.greenhouse.io/dropbox/jobs/12345") == "ATS"
    assert classify_url_destination("https://jobs.lever.co/spotify/67890") == "ATS"
    workday_url = "https://mycompany.myworkdayjobs.com/en-US/careers/job/1"
    assert classify_url_destination(workday_url) == "ATS"
    assert classify_url_destination("https://jobs.smartrecruiters.com/AcmeCorp/123") == "ATS"
    assert classify_url_destination("https://apply.workable.com/tech-start/j/ABC/") == "ATS"
    assert classify_url_destination("https://acme.bamboohr.com/careers/12") == "ATS"
    assert classify_url_destination("https://jobs.ashbyhq.com/scale/123") == "ATS"


def test_classify_url_destination_aggregator():
    assert classify_url_destination("https://za.indeed.com/viewjob?jk=123") == "AGGREGATOR"
    assert classify_url_destination("https://www.pnet.co.za/jobs/developer-12345") == "AGGREGATOR"
    assert classify_url_destination("https://www.careers24.com/jobs/ad/6789") == "AGGREGATOR"
    assert classify_url_destination("https://www.linkedin.com/jobs/view/12345") == "AGGREGATOR"
    assert classify_url_destination("https://www.glassdoor.com/job-listing/123") == "AGGREGATOR"


def test_classify_url_destination_employer_direct():
    google_careers = "https://careers.google.com/jobs/results/123"
    assert classify_url_destination(google_careers) == "EMPLOYER_DIRECT"
    acme_careers = "https://www.acmecorp.co.za/careers/software-eng"
    assert classify_url_destination(acme_careers) == "EMPLOYER_DIRECT"


def test_extract_candidate_links_prioritizes_ats():
    html = """
    <div>
      <a href="https://za.indeed.com/cmp/acme">Company Profile</a>
      <a href="https://boards.greenhouse.io/acme/jobs/42" class="apply">Apply on Company Site</a>
      <a href="https://careers.acme.com/apply">Alternative Apply</a>
    </div>
    """
    links = extract_candidate_links_from_html(html)
    assert len(links) >= 2
    assert links[0] == "https://boards.greenhouse.io/acme/jobs/42"


def test_resolve_preferred_destination_from_aggregator_page():
    html = """
    <html>
      <body>
        <div class="apply-bar">
          <a href="https://jobs.lever.co/acme/apply">Apply Now</a>
        </div>
      </body>
    </html>
    """
    discovery_url = "https://za.indeed.com/viewjob?jk=abc"
    resolved_url, dest_type = LinkResolver.resolve_preferred_destination(discovery_url, html)
    assert resolved_url == "https://jobs.lever.co/acme/apply"
    assert dest_type == "ATS"


def test_resolve_preferred_destination_retains_direct_employer():
    direct_url = "https://acme.com/careers/openings/123"
    resolved_url, dest_type = LinkResolver.resolve_preferred_destination(direct_url)
    assert resolved_url == direct_url
    assert dest_type == "EMPLOYER_DIRECT"
