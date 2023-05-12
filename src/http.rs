use anyhow::{bail, Context, Result};
use log::{debug, error};
use serde_json::Value;
use std::sync::mpsc::{channel, Sender};
use std::thread;
use std::time::Duration;

struct GeoIPService {
    url: &'static str,
    tz_keys: &'static [&'static str],
}

/// {ip} will be replaced with the IP. Services must be able to take {ip} being replaced with "" as
/// meaning to use the source IP for the request.
static SERVICES: &[GeoIPService] = &[
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
    let res = ureq::get(&url).call()?;
    let val = match get_nested_value(res.into_json()?, service.tz_keys)
        .context("Invalid data for {url}")?
    {
        Value::String(s) => s,
        _ => bail!("Timezone field for {url} is not a string"),
    };
    debug!("Sending {val} back to main thread from {url}");

    // Only fails if receiver is disconnected, which just means we lost the race
    let _ = sender.send(val);
    Ok(())
}

/// Spawn background HTTP requests, getting the first timezone returned.
pub fn get_timezone(ip_addr: String, timeout: Duration) -> Result<String> {
    let (sender, receiver) = channel();
    for svc in SERVICES {
        let sender = sender.clone();
        let url = svc.url.replace("{ip}", &ip_addr);
        // For our small number of services, this makes more sense than using a full async runtime
        thread::spawn(move || {
            if let Err(err) = get_timezone_for_ip(url, svc, sender) {
                error!("{err}");
            }
        });
    }
    receiver
        .recv_timeout(timeout)
        .context("Timed out, consider increasing --timeout")
}
