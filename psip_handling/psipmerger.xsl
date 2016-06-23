<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:pcmp="http://www.atsc.org/XMLSchemas/pmcp/2007/3.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.atsc.org/XMLSchemas/pmcp/2007/3.1 PMCP31.xsd" destination="PSIP Generator" type="information" exclude-result-prefixes="xsi pcmp">
<xsl:param name="psipnycmg"/>
<xsl:output encoding="UTF-8" method="xml" version="1.0" indent="yes"/>
  <xsl:template match="/">
    <PmcpMessage xmlns="http://www.atsc.org/XMLSchemas/pmcp/2007/3.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.atsc.org/XMLSchemas/pmcp/2007/3.1 PMCP31.xsd">
        <xsl:attribute name="origin">ProTrack</xsl:attribute>
        <xsl:attribute name="originType">Traffic</xsl:attribute>
        <xsl:attribute name="destination">PSIP Generator</xsl:attribute>
        <xsl:attribute name="dateTime">2013-04-03T10:59:40.76-04:00</xsl:attribute>
        <!--<xsl:attribute name="xmlns">http://www.atsc.org/XMLSchemas/pmcp/2007/3.1</xsl:attribute>-->
        <xsl:attribute name="id">1</xsl:attribute>
        <xsl:attribute name="type">information</xsl:attribute>
        <xsl:copy-of select="/pcmp:PmcpMessage/pcmp:Channel"/>
        <xsl:copy-of select="document($psipnycmg)/pcmp:PmcpMessage/pcmp:Channel"/>
        <xsl:for-each select="/pcmp:PmcpMessage/pcmp:PsipEvent|document($psipnycmg)/pcmp:PmcpMessage/pcmp:PsipEvent">
          <PsipEvent>
            <xsl:attribute name="startTime"><xsl:value-of select="@startTime"/></xsl:attribute>
            <xsl:attribute name="duration"><xsl:value-of select="@duration"/></xsl:attribute>
            <xsl:copy-of select="pcmp:EventId"/>
            <ShowData>
              <xsl:copy-of select="pcmp:ShowData/pcmp:Name"/>
              <Description>
                <xsl:if test="pcmp:ShowData/pcmp:Description/@lang">
                  <xsl:attribute name="lang">
                    <xsl:value-of select="pcmp:ShowData/pcmp:Description/@lang"/>
                  </xsl:attribute>
                </xsl:if>
                <xsl:if test="normalize-space(pcmp:ShowData/pcmp:Description)">
                  <xsl:value-of select="normalize-space(pcmp:ShowData/pcmp:Description)"/>
                </xsl:if>
              </Description>
              <xsl:copy-of select="pcmp:ShowData/pcmp:ParentalRating"/>
              <xsl:copy-of select="pcmp:ShowData/pcmp:Audios"/>
              <Captions>
                <xsl:if test="pcmp:ShowData/pcmp:Captions/pcmp:Caption608">
                  <Caption608>
                    <xsl:if test="pcmp:ShowData/pcmp:Captions/pcmp:Caption608/@service">
                      <xsl:attribute name="service">
                        <xsl:value-of select="pcmp:ShowData/pcmp:Captions/pcmp:Caption608/@service"/>
                      </xsl:attribute>
                    </xsl:if>
                    <xsl:if test="pcmp:ShowData/pcmp:Captions/pcmp:Caption608/@lang">
                      <xsl:attribute name="lang">
                        <xsl:choose>
                          <xsl:when test="pcmp:ShowData/pcmp:Captions/pcmp:Caption608/@lang='n/a'">
                            <xsl:text>und</xsl:text>
                          </xsl:when>
                          <xsl:otherwise>
                            <xsl:value-of select="pcmp:ShowData/pcmp:Captions/pcmp:Caption608/@lang"/>
                          </xsl:otherwise>
                        </xsl:choose>
                      </xsl:attribute>
                    </xsl:if>
                  </Caption608>
                </xsl:if>
                <xsl:if test="pcmp:ShowData/pcmp:Captions/pcmp:Caption708">
                  <Caption708>
                    <xsl:if test="pcmp:ShowData/pcmp:Captions/pcmp:Caption708/@service">
                      <xsl:attribute name="service">
                        <xsl:value-of select="pcmp:ShowData/pcmp:Captions/pcmp:Caption708/@service"/>
                      </xsl:attribute>
                    </xsl:if>
                    <xsl:if test="pcmp:ShowData/pcmp:Captions/pcmp:Caption708/@lang">
                      <xsl:attribute name="lang">
                        <xsl:choose>
                          <xsl:when test="pcmp:ShowData/pcmp:Captions/pcmp:Caption708/@lang='n/a'">
                            <xsl:text>und</xsl:text>
                          </xsl:when>
                          <xsl:otherwise>
                            <xsl:value-of select="pcmp:ShowData/pcmp:Captions/pcmp:Caption708/@lang"/>
                          </xsl:otherwise>
                        </xsl:choose>
                      </xsl:attribute>
                    </xsl:if>
                  </Caption708>
                </xsl:if>
                <xsl:if test="pcmp:ShowData/pcmp:Captions/Null">
                  <Null/>
                </xsl:if>
              </Captions>
            </ShowData>
          </PsipEvent>
        </xsl:for-each>
    </PmcpMessage>
  </xsl:template>
</xsl:stylesheet>
