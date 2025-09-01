use anyhow::{anyhow, bail, Context, Result};
use log::debug;
use serde_json::Value;
use std::cmp::Reverse;
use std::collections::HashMap;
use std::sync::mpsc::{channel, Receiver, RecvTimeoutError, Sender};
use std::thread;
use std::time::{Duration, Instant};

struct GeoIPService {
    url: &'static str,
    tz_keys: &'static [&'static str],
}

struct Tally {
    count: usize,
    first_seen: usize,
}

struct SpawnedRequests {
    receiver: Receiver<String>,
    svc_count: usize,
}

/// {ip} will be replaced with the IP. Services must be able to take {ip} being replaced with "" as
/// meaning to use the source IP for the request.
static SERVICES: &[GeoIPService] = &[
    GeoIPService {
        url: "https://geoip.chrisdown.name/{ip}",
        tz_keys: &["location", "time_zone"],
    },
    GeoIPService {
        url: "https://api.ipbase.com/v1/json/{ip}",
        tz_keys: &["time_zone"],
    },
    GeoIPService {
        url: "https://ipapi.co/{ip}/json/",
        tz_keys: &["timezone"],
    },
    GeoIPService {
        url: "https://worldtimeapi.org/api/ip/{ip}",
        tz_keys: &["timezone"],
    },
    GeoIPService {
        url: "https://reallyfreegeoip.org/json/{ip}",
        tz_keys: &["time_zone"],
    },
    GeoIPService {
        url: "https://ipwho.is/{ip}",
        tz_keys: &["timezone", "id"],
    },
    GeoIPService {
        url: "https://ipinfo.io/{ip}/json",
        tz_keys: &["timezone"],
    },
];

/// Given &["foo", "bar", "baz"], retrieve the value at data["foo"]["bar"]["baz"].
fn get_nested_value(mut data: Value, keys: &[&str]) -> Option<Value> {
    for key in keys {
        match data {
            Value::Object(mut map) => {
                data = map.remove(*key)?;
            }
            _ => return None,
        }
    }

    Some(data)
}

/// A single service worker, racing with others as part of `get_timezone`.
fn get_timezone_for_ip(url: String, service: &GeoIPService, sender: Sender<String>) -> Result<()> {
    let mut res = ureq::get(&url).call()?;
    let val = match get_nested_value(res.body_mut().read_json()?, service.tz_keys)
        .with_context(|| format!("Invalid data for {url}"))?
    {
        Value::String(s) => s,
        _ => bail!("Timezone field for {url} is not a string"),
    };
    debug!("Sending {val} back to main thread from {url}");

    // Only fails if receiver is disconnected, which just means we lost the race
    let _ = sender.send(val);
    Ok(())
}

/// Spawn workers for all SERVICES and return a handle for their responses.
fn spawn_requests(ip_addr: &str) -> SpawnedRequests {
    let (sender, receiver) = channel();

    for (svc, sender) in SERVICES.iter().zip(std::iter::repeat(sender)) {
        let url = svc.url.replace("{ip}", ip_addr);
        // For our small number of services, this makes more sense than using a full async runtime
        thread::spawn(move || {
            if let Err(err) = get_timezone_for_ip(url, svc, sender) {
                debug!("{err}");
            }
        });
    }

    SpawnedRequests {
        receiver,
        svc_count: SERVICES.len(),
    }
}

/// Spawn background HTTP requests, returning the first timezone that replies.
pub fn get_timezone_first(ip_addr: String, timeout: Duration) -> Result<String> {
    let SpawnedRequests { receiver, .. } = spawn_requests(&ip_addr);

    receiver.recv_timeout(timeout).map_err(|err| match err {
        RecvTimeoutError::Disconnected => {
            anyhow!("All APIs failed. Run with RUST_LOG=tzupdate=debug for more information.")
        }
        RecvTimeoutError::Timeout => anyhow!("All APIs timed out, consider increasing --timeout."),
    })
}

/// Spawn background HTTP requests, collecting responses and choosing by consensus.
/// If a strict majority (> 50%) is reached before the timeout, return immediately.
/// Otherwise, after the timeout or when all responses are in, return the most frequent
/// timezone seen. Ties are broken by the earliest response among the tied values.
pub fn get_timezone_consensus(ip_addr: String, timeout: Duration) -> Result<String> {
    let SpawnedRequests {
        receiver,
        svc_count,
    } = spawn_requests(&ip_addr);

    let deadline = Instant::now() + timeout;
    let majority = svc_count / 2 + 1;

    let mut tallies = HashMap::new();
    let mut seen_idx = 0usize;
    let mut timed_out = false;

    loop {
        let now = Instant::now();
        if now >= deadline {
            timed_out = true;
            break;
        }

        match receiver.recv_timeout(deadline.saturating_duration_since(now)) {
            Ok(tz) => {
                seen_idx += 1;
                let entry = tallies.entry(tz.clone()).or_insert(Tally {
                    count: 0,
                    first_seen: seen_idx,
                });
                entry.count += 1;

                if entry.count >= majority {
                    return Ok(tz);
                }

                if seen_idx == svc_count {
                    break;
                }
            }
            Err(RecvTimeoutError::Timeout) => {
                timed_out = true;
                break;
            }
            Err(RecvTimeoutError::Disconnected) => break,
        }
    }

    if tallies.is_empty() {
        if timed_out {
            bail!("All APIs timed out, consider increasing --timeout.");
        }
        bail!("All APIs failed. Run with RUST_LOG=tzupdate=debug for more information.");
    }

    let (best_tz, _) = tallies
        .into_iter()
        .max_by_key(|(_, tally)| (tally.count, Reverse(tally.first_seen)))
        .unwrap();

    Ok(best_tz)
}
