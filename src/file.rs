use anyhow::{bail, Context, Result};
use log::debug;
use std::fs;
use std::io::{self, Write};
use std::os::linux::fs::MetadataExt;
use std::os::unix::fs::{symlink, OpenOptionsExt};
use std::path::{Path, PathBuf};

/// Canonicalise `path`, checking for directory traversal outside of `base`.
///
/// Since we are linking based upon the output of some data we retrieved over the internet, we
/// should check that the output doesn't attempt to do something naughty with local path traversal.
///
/// This function checks that the base directory of the zoneinfo database shares a common prefix
/// with the absolute path of the requested zoneinfo file.
fn safe_canonicalise_path(base: &Path, path: &Path) -> io::Result<PathBuf> {
    let base = fs::canonicalize(base)?;
    let path = fs::canonicalize(path)?;
    if path.starts_with(&base) {
        Ok(path)
    } else {
        Err(io::Error::new(
            io::ErrorKind::Other,
            format!(
                "Directory traversal detected, {} is outside of {}",
                path.display(),
                base.display()
            ),
        ))
    }
}

/// Given a file that we eventually want to atomically rename to, give us a temporary path that we
/// can use in the interim.
///
/// This must be in the same directory as `path` because we will later call `fs::rename` on it,
/// which is only atomic when not cross device.
fn get_tmp_path(path: &Path) -> Result<PathBuf> {
    tempfile::Builder::new()
        .tempfile_in(
            path.parent()
                .context("Refusing to create temp file in root")?,
        )?
        .into_temp_path()
        .canonicalize()
        .map_err(anyhow::Error::from)
}

/// Atomically link to a timezone file from the zoneinfo db from `localtime_path`.
///
/// Since we may be retrieving the timezone file's relative path from an untrusted source, we also
/// do checks to make sure that no directory traversal is going on. See `safe_canonicalise_path`
/// for information about how that works.
pub fn link_localtime(
    timezone: &str,
    localtime_path: PathBuf,
    zoneinfo_path: PathBuf,
) -> Result<()> {
    let localtime_tmp_path = get_tmp_path(&localtime_path)?;
    let unsafe_tz_path = zoneinfo_path.join(timezone);
    let tz_path = match safe_canonicalise_path(&zoneinfo_path, &unsafe_tz_path) {
        Ok(path) => path,
        Err(err) if err.kind() == io::ErrorKind::NotFound => {
            bail!("Timezone \"{timezone}\" requested, but this timezone is not available on your operating system.");
        }
        Err(err) => bail!(err),
    };

    if let Err(err) = fs::remove_file(&localtime_tmp_path) {
        if err.kind() != io::ErrorKind::NotFound {
            bail!(err);
        }
    }

    debug!(
        "Symlinking {} to {}",
        localtime_tmp_path.display(),
        tz_path.display()
    );
    symlink(tz_path, &localtime_tmp_path)?;

    // We should seek to avoid avoid /etc/localtime disappearing, even briefly, to avoid
    // applications being unhappy -- that's why we insist on atomic rename.
    if localtime_tmp_path.metadata()?.st_dev() != localtime_path.metadata()?.st_dev() {
        fs::remove_file(&localtime_tmp_path)?;
        bail!(
            "Cannot atomically rename, {} and {} are not on the same device",
            localtime_tmp_path.display(),
            localtime_path.display()
        );
    }

    debug!(
        "Atomically renaming {} to {}",
        localtime_tmp_path.display(),
        localtime_path.display()
    );
    fs::rename(localtime_tmp_path, localtime_path)?;

    Ok(())
}

/// Debian and derivatives also have /etc/timezone, which is used for a human readable timezone.
/// Without this, dpkg-reconfigure will nuke /etc/localtime on reconfigure.
///
/// If `always_write` is false, we will skip when /etc/timezone doesn't exist.
pub fn write_timezone(timezone: &str, filename: PathBuf, always_write: bool) -> io::Result<()> {
    let mut file = match fs::OpenOptions::new()
        .write(true)
        .create(always_write)
        .mode(0o644)
        .open(&filename)
    {
        Ok(file) => file,
        Err(err) if err.kind() == io::ErrorKind::NotFound => {
            debug!("{} does not exist, not writing to it", filename.display());
            return Ok(());
        }
        Err(err) => return Err(err),
    };
    let data = format!("{timezone}\n");
    file.write_all(data.as_bytes())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonicalise_normal() {
        let base = PathBuf::from("/etc");
        let path = PathBuf::from("/etc/passwd");
        assert!(safe_canonicalise_path(&base, &path).is_ok());
    }

    #[test]
    fn canonicalise_back_and_forth() {
        let base = PathBuf::from("/etc");
        let path = PathBuf::from("/etc/../etc/passwd");
        assert!(safe_canonicalise_path(&base, &path).is_ok());
    }

    #[test]
    fn canonicalise_failure() {
        let base = PathBuf::from("/etc");
        let path = PathBuf::from("/etc/../passwd");
        assert!(safe_canonicalise_path(&base, &path).is_err());
    }
}
