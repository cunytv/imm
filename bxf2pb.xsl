<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:bxf="http://smpte-ra.org/schemas/2021/2008/BXF" exclude-result-prefixes="xsl bxf">
    <xsl:output encoding="UTF-8" method="xml" version="1.0" indent="yes"/>
    <xsl:template match="bxf:BxfMessage">
        <xsl:apply-templates select="bxf:BxfData/bxf:Schedule"/>
    </xsl:template>
    <xsl:template match="bxf:BxfMessage/bxf:BxfData/bxf:Schedule">
        <playlist>
            <eventlist>
                <xsl:for-each select="bxf:ScheduledEvent[bxf:EventData/@eventType='Primary']">
                    <event>
                        <xsl:attribute name="type">MEDIA</xsl:attribute>
                        <stream>0</stream>
                        <!-- convert @broadcastDate and SmpteTimeCode to ISO8601 -->
                        <onairtime>
                            <xsl:value-of select="bxf:EventData/bxf:StartDateTime/bxf:SmpteDateTime/@broadcastDate"/>
                            <xsl:text>T</xsl:text>
                            <xsl:value-of select="bxf:EventData/bxf:StartDateTime/bxf:SmpteDateTime/bxf:SmpteTimeCode"/>
                        </onairtime>
                        <!-- set start time based on pattern-matching -->
                        <starttype>
                            <xsl:choose>
                                <xsl:when test="contains(bxf:EventData/bxf:StartDateTime/bxf:SmpteDateTime/bxf:SmpteTimeCode,'00:00')">
                                    <xsl:text>FIX</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>SEQ</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </starttype>
                        <endtype>NORM</endtype>
                        <mediaid><xsl:value-of select="bxf:Content/bxf:ContentId/bxf:HouseNumber"/></mediaid>
                        <houseid></houseid>
                        <reconcilekey><xsl:value-of select="bxf:EventData/bxf:EventId/bxf:EventId"/></reconcilekey>
                        <title><xsl:value-of select="bxf:Content/bxf:Name"/></title>
                        <category>?</category>
                        <som><xsl:value-of select="bxf:Content/bxf:Media/bxf:MediaLocation/bxf:SOM/bxf:SmpteTimeCode"/></som>
                        <duration><xsl:value-of select="bxf:Content/bxf:Media/bxf:MediaLocation/bxf:Duration/bxf:SmpteDuration/bxf:SmpteTimeCode"/></duration>
                        <!-- fixed effect -->
                        <effect>FadeFade</effect>
                        <!-- fixed rate -->
                        <rate>Medium</rate>
                        <subtitles/>
                        <vps/>
                        <secondaryeventlist>
                            <xsl:if test="following-sibling::bxf:ScheduledEvent[1]/bxf:EventData/@eventType='NonPrimary'">
                                <secondaryevent type="Keyer">
                                    <starttype origin="+Start" offset="00:00:30;00"/>
                                    <endtype origin="-End" offset="00:00:30;00"/>
                                    <customdata>
                                        <rate>0</rate>
                                        <logoname><xsl:value-of select="following-sibling::bxf:ScheduledEvent[1]/bxf:Content/bxf:ContentId/bxf:HouseNumber"/></logoname>
                                        <fxno>12</fxno>
                                        <tran>0</tran>
                                    </customdata>
                                </secondaryevent>
                            </xsl:if>
                            <xsl:if test="bxf:Content/bxf:Media/bxf:PrecompressedTS/bxf:TSVideo/bxf:PrivateInformation/bxf:ScreenFormatText != 'SD-FF' and bxf:Content/bxf:Media/bxf:PrecompressedTS/bxf:TSVideo/bxf:PrivateInformation/bxf:ScreenFormatText != 'HD-FF'">
                              <secondaryevent>
                                <xsl:attribute name="type">
                                    <xsl:value-of select="bxf:Content/bxf:Media/bxf:PrecompressedTS/bxf:TSVideo/bxf:PrivateInformation/bxf:ScreenFormatText"/>
                                </xsl:attribute>
                                <starttype origin="+Start" offset="00:00:00;00"/>
                                <endtype origin="-End" offset="00:00:00;00"/>
                            </secondaryevent>
                            </xsl:if>
                        </secondaryeventlist>
                        <eventnote><xsl:value-of select="bxf:Series/bxf:EpisodeName"/></eventnote>
                    </event>
                </xsl:for-each>
            </eventlist>
        </playlist>
    </xsl:template>
</xsl:stylesheet>