use anyhow::Result;
use clap::Parser;
use log::info;
use std::path::PathBuf;
use std::time::Duration;

mod file;
mod http;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Config {
    #[arg(
        short,
        long,
        help = "print the timezone, but don't update /etc/timezone or /etc/localtime"
    )]
    print_only: bool,

    #[arg(
        short,
        long,
        help = "use this IP instead of automatically detecting it"
    )]
    ip: Option<String>,

    #[arg(
        short,
        long,
        help = "use this timezone instead of automatically detecting it"
    )]
    timezone: Option<String>,

    #[arg(
        short,
        long,
        help = "path to root of the zoneinfo database",
        default_value = "/usr/share/zoneinfo"
    )]
    zoneinfo_path: PathBuf,

    #[arg(
        short,
        long,
        help = "path to localtime symlink",
        default_value = "/etc/localtime"
    )]
    localtime_path: PathBuf,

    #[arg(
        short,
        long,
        help = "path to Debian timezone name file",
        default_value = "/etc/timezone"
    )]
    debian_timezone_path: PathBuf,

    #[arg(long, help = "create Debian timezone file even if it doesn't exist")]
    always_write_debian_timezone: bool,

    #[arg(
        short = 's',
        long,
        help = "maximum number of seconds to wait for APIs to return",
        value_parser = parse_secs,
        default_value = "30"
    )]
    timeout: Duration,
}

fn parse_secs(arg: &str) -> Result<Duration> {
    Ok(Duration::from_secs(arg.parse()?))
}

fn main() -> Result<()> {
    env_logger::init_from_env(env_logger::Env::default().default_filter_or("warn"));

    let cfg = Config::parse();
    let tz = match cfg.timezone {
        Some(tz) => tz,
        None => http::get_timezone(cfg.ip.unwrap_or_default(), cfg.timeout)?,
    };

    if cfg.print_only {
        println!("{tz}");
        return Ok(());
    }

    info!("Got timezone {tz}");
    file::link_localtime(&tz, cfg.localtime_path, cfg.zoneinfo_path)?;
    file::write_timezone(
        &tz,
        cfg.debian_timezone_path,
        cfg.always_write_debian_timezone,
    )?;
    println!("Set system timezone to {tz}.");

    Ok(())
}
