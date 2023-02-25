package com.example.slice_simple;

import android.telephony.CellSignalStrengthNr;
import android.telephony.SignalStrength;
import android.telephony.TelephonyCallback;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 监听信号强度变化 通过map对外开放信号强度三元组
 */
public class SigStrengthListener extends TelephonyCallback implements TelephonyCallback.SignalStrengthsListener {

    public Map<String, Integer> SignalStr = new HashMap<>(); //含有无线信号强度与功率三个数据
    private static SigStrengthListener INSTANCE = new SigStrengthListener();

    private SigStrengthListener(){

    }

    public Map<String, Integer> getSignalStr() {
        return SignalStr;
    }

    public static SigStrengthListener getINSTANCE() {
        return INSTANCE;
    }

    @Override
    public void onSignalStrengthsChanged(SignalStrength ss){
        List<CellSignalStrengthNr> strengthNrList = ss.getCellSignalStrengths(CellSignalStrengthNr.class);
        if(!strengthNrList.isEmpty()) {
            System.out.println("Signal Strength Change");
            CellSignalStrengthNr css = strengthNrList.get(0);
            int dbm = css.getDbm();
            int ssRsrp = css.getSsRsrp();
            int ssRsrq = css.getSsRsrq();   //-10,[-15,-10],[-20,-15],-20
//           System.out.println("dbm: " + dbm);//事实上就是ssRsrp  >=-80excellent [-90,-80]Good [-100,-90]MidCell, <=-100 小区边缘
//           System.out.println("ssRsrp:" + ssRsrp);
//           System.out.println("ssRsrq:" + ssRsrq);
            SignalStr.put("dbm", dbm);
            SignalStr.put("ssRsrp", ssRsrp);
            SignalStr.put("ssRsrq", ssRsrq);
            //TODO:判断出较差时触发切片判断
        }
    }
}
