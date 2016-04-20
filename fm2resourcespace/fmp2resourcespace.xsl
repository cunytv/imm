<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:fmp="http://www.filemaker.com/fmpxmlresult" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLoaction="http://www.pbcore.org/PBCore/PBCoreNamespace.html" exclude-result-prefixes="fmp xsi">
    <!--
    
    Note that metadata may be pulled from filemaker server via this url convention:
        http://10.10.200.28/fmi/xml/FMPXMLRESULT.xml?-db=CUNY_TV_archive&-lay=remoteimport&PBCoreIdentifier::identifier=EWM00105&-find
        replace EWM00105 with the mediaid requested
    
    -->
    <xsl:output encoding="UTF-8" method="xml" version="1.0" indent="yes" omit-xml-declaration="yes"/>
    <xsl:key name="N" match="/fmp:FMPXMLRESULT/fmp:METADATA/fmp:FIELD" use="@NAME"/>
    <xsl:key name="N" match="/fmp:FMPXMLRESULT/fmp:METADATA/fmp:FIELD" use="following-sibling::fmp:FIELD/@NAME"/>
    <xsl:template match="fmp:FMPXMLRESULT">
        <xsl:apply-templates select="fmp:RESULTSET"/>
    </xsl:template>
    <xsl:template match="fmp:FMPXMLRESULT/fmp:RESULTSET">
        <xsl:if test="count(fmp:ROW)>0">
            <resourceset>
                <xsl:for-each select="fmp:ROW[1]">
                    <xsl:variable name="row_pos" select="position()"/>
                    <xsl:variable name="asset_pk">
                        <xsl:value-of select="fmp:COL[count(key('N','asset_serial_pk'))]/fmp:DATA"/>
                    </xsl:variable>
                    <resource>
                        <xsl:attribute name="type">3</xsl:attribute>
                        <keyfield>
                            <xsl:attribute name="ref">8</xsl:attribute>
                            <xsl:value-of select="fmp:COL[count(key('N','PBCoreIdentifier_mediaid'))]/fmp:DATA[$row_pos]"/>
                        </keyfield>
                        <!--
                        <collection>
                            <xsl:value-of select="fmp:COL[count(key('N','PBCoreTitle::title'))]/fmp:DATA"/>
                        </collection>
                        -->
                        <xsl:if test="fmp:COL[count(key('N', 'PBCoreIdentifier::identifier'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">78</xsl:attribute><!-- identifiers -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreIdentifier::identifier'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreIdentifier::identifierSource'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCoreAssetType::assetType'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">77</xsl:attribute><!-- assettype -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreAssetType::assetType'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                        <xsl:if test="fmp:COL[count(key('N', 'PBCoreCoverage::coverage'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">93</xsl:attribute><!-- coverage -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreCoverage::coverage'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreCoverage::type'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                        </xsl:if>
                        <xsl:if test="fmp:COL[count(key('N', 'PBCoreDate::datevalue'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">82</xsl:attribute><!-- dates -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreDate::datevalue'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreDate::dateType'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCoreTitle_series'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">73</xsl:attribute><!-- title series -->
                            <xsl:value-of select="fmp:COL[count(key('N','PBCoreTitle_series'))]/fmp:DATA[$row_pos]"/>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCoreTitle_episode'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">76</xsl:attribute><!-- title episode -->
                            <xsl:value-of select="fmp:COL[count(key('N','PBCoreTitle_episode'))]/fmp:DATA[$row_pos]"/>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCoreTitle::title'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">111</xsl:attribute><!-- titles -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreTitle::title'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreTitle::titleType'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCoreDescription::description'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">84</xsl:attribute><!-- descriptions -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreDescription::description'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreDescription::descriptionType'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCoreCreator::creator'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">86</xsl:attribute><!-- creators -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreCreator::creator'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreCreator::creatorRole'))]/fmp:DATA[$pos]"/><!-- is this right -->
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCoreContributor::contributor'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">90</xsl:attribute><!-- contributors -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreContributor::contributor'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreContributor::affiliation'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCoreRole_Contributor::role'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCorePublisher::publisher'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">91</xsl:attribute><!-- publishers -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCorePublisher::publisher'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="../../fmp:COL[count(key('N', 'PBCorePublisher::publisherRole'))]/fmp:DATA[$pos]"/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                      <xsl:if test="fmp:COL[count(key('N', 'PBCoreInstantiation::display_Instantiation_w_related_summary'))]/fmp:DATA">
                        <field>
                            <xsl:attribute name="ref">116</xsl:attribute><!-- instantiations -->
                            <xsl:for-each select="fmp:COL[count(key('N', 'PBCoreInstantiation::display_Instantiation_w_related_summary'))]/fmp:DATA">
                                <xsl:variable name="pos" select="position()"/>
                                <xsl:text>&lt;tr&gt;&lt;td&gt;</xsl:text>
                                <xsl:value-of select="."/>
                                <xsl:text>&lt;/td&gt;&lt;/tr&gt;</xsl:text>
                            </xsl:for-each>
                        </field>
                      </xsl:if>
                    </resource>
                </xsl:for-each>
            </resourceset>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>
