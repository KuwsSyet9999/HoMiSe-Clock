package com.homise.clock

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat

/**
 * 当前电量百分比（0..100，整数）；读不到时返回 -1。
 *
 * 用 `ACTION_BATTERY_CHANGED` 而非轮询 `BATTERY_PROPERTY_CAPACITY`：
 * 前者是**粘性广播**，注册那一刻系统就会立即回传一次当前值，之后电量变化再推送，
 * 既不需要定时器也不会有刷新延迟。
 *
 * 该广播由**系统**发出，因此注册时必须用 `RECEIVER_EXPORTED`。
 * 曾误用 `RECEIVER_NOT_EXPORTED`（只能收到本应用发出的广播），结果系统广播收不到、
 * 电量始终为 -1，电块干脆不显示——而且只在重启后才暴露（首次安装时广播恰好已缓存）。
 * 读取电量本身仍然不需要任何权限。
 */
@Composable
fun rememberBatteryPercent(): Int {
    val context = LocalContext.current
    var percent by remember { mutableStateOf(-1) }

    DisposableEffect(context) {
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context?, intent: Intent?) {
                val level = intent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
                val scale = intent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
                if (level >= 0 && scale > 0) {
                    // 四舍五入取整：某些设备的 level/scale 比例会落在 .5 附近
                    percent = (level * 100 + scale / 2) / scale
                }
            }
        }
        // 注册失败不应拖垮界面（例如预览环境没有真实系统服务），此时保持 -1 即"不显示"
        val registered = try {
            ContextCompat.registerReceiver(
                context,
                receiver,
                IntentFilter(Intent.ACTION_BATTERY_CHANGED),
                // 必须 EXPORTED：ACTION_BATTERY_CHANGED 来自系统进程，
                // NOT_EXPORTED 会把系统广播一并挡掉，导致电量永远读不到。
                ContextCompat.RECEIVER_EXPORTED,
            )
            true
        } catch (e: Exception) {
            false
        }
        onDispose { if (registered) runCatching { context.unregisterReceiver(receiver) } }
    }

    return percent
}
